import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { authAPI } from '../services/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/tabs';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/ui/card';
import { toast } from 'sonner';
import { Shield, Lock, Mail, Phone, User, Key } from 'lucide-react';

const Auth = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [activeTab, setActiveTab] = useState('customer');
  const [mode, setMode] = useState('login'); // 'login' or 'signup'
  
  // Signup state
  const [signupData, setSignupData] = useState({
    username: '',
    email: '',
    phone: '',
    password: '',
    role: 'customer'
  });
  const [signupOTP, setSignupOTP] = useState('');
  const [signupTarget, setSignupTarget] = useState('');
  const [showSignupOTP, setShowSignupOTP] = useState(false);
  
  // Login state
  const [loginData, setLoginData] = useState({
    identifier: '',
    password: ''
  });
  const [loginOTP, setLoginOTP] = useState('');
  const [loginTarget, setLoginTarget] = useState('');
  const [showLoginOTP, setShowLoginOTP] = useState(false);
  const [loginUsername, setLoginUsername] = useState('');
  
  const [loading, setLoading] = useState(false);

  // Handle Signup
  const handleSignup = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const payload = {
        ...signupData,
        role: activeTab
      };
      
      const response = await authAPI.signup(payload);
      setSignupTarget(response.data.target);
      setShowSignupOTP(true);
      toast.success(response.data.message);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Signup failed');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifySignup = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await authAPI.verifySignup({
        target: signupTarget,
        otp: signupOTP,
        purpose: 'signup'
      });
      toast.success('Account verified! Please login.');
      setMode('login');
      setShowSignupOTP(false);
      setSignupOTP('');
      setSignupData({
        username: '',
        email: '',
        phone: '',
        password: '',
        role: 'customer'
      });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Verification failed');
    } finally {
      setLoading(false);
    }
  };

  // Handle Login
  const handleLoginPassword = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await authAPI.loginPassword(loginData);
      setLoginTarget(response.data.target);
      setLoginUsername(response.data.username);
      setShowLoginOTP(true);
      toast.success(response.data.message);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyLoginOTP = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await authAPI.verifyLoginOTP({
        target: loginTarget,
        otp: loginOTP,
        purpose: 'login'
      });
      
      const tokens = response.data;
      
      // Fetch user info
      const userResponse = await authAPI.signup({ username: loginUsername });
      
      login(tokens, { username: loginUsername, role: activeTab });
      toast.success('Login successful!');
      
      // Navigate based on role
      if (activeTab === 'admin') {
        navigate('/admin');
      } else {
        navigate('/customer');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'OTP verification failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-white rounded-2xl shadow-lg mb-4">
            <Shield className="w-10 h-10 text-purple-600" />
          </div>
          <h1 className="text-4xl font-bold text-white mb-2">Secure Auth</h1>
          <p className="text-purple-100">Advanced authentication system with 2FA</p>
        </div>

        <Card className="shadow-2xl border-0">
          <CardHeader className="space-y-1 pb-4">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-2 mb-4">
                <TabsTrigger value="customer" data-testid="customer-tab">
                  <User className="w-4 h-4 mr-2" />
                  Customer
                </TabsTrigger>
                <TabsTrigger value="admin" data-testid="admin-tab">
                  <Shield className="w-4 h-4 mr-2" />
                  Admin
                </TabsTrigger>
              </TabsList>
            </Tabs>
            
            <div className="flex gap-2 justify-center pt-2">
              <Button
                variant={mode === 'login' ? 'default' : 'outline'}
                onClick={() => setMode('login')}
                className="flex-1"
                data-testid="login-mode-btn"
              >
                Login
              </Button>
              <Button
                variant={mode === 'signup' ? 'default' : 'outline'}
                onClick={() => setMode('signup')}
                className="flex-1"
                data-testid="signup-mode-btn"
              >
                Sign Up
              </Button>
            </div>
          </CardHeader>

          <CardContent>
            {mode === 'signup' ? (
              !showSignupOTP ? (
                <form onSubmit={handleSignup} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="signup-username">Username</Label>
                    <div className="relative">
                      <User className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="signup-username"
                        placeholder="Enter username"
                        value={signupData.username}
                        onChange={(e) => setSignupData({ ...signupData, username: e.target.value })}
                        required
                        className="pl-10"
                        data-testid="signup-username-input"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="signup-email">Email (Optional)</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="signup-email"
                        type="email"
                        placeholder="Enter email"
                        value={signupData.email}
                        onChange={(e) => setSignupData({ ...signupData, email: e.target.value })}
                        className="pl-10"
                        data-testid="signup-email-input"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="signup-phone">Phone (Optional)</Label>
                    <div className="relative">
                      <Phone className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="signup-phone"
                        placeholder="+1234567890"
                        value={signupData.phone}
                        onChange={(e) => setSignupData({ ...signupData, phone: e.target.value })}
                        className="pl-10"
                        data-testid="signup-phone-input"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="signup-password">Password</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="signup-password"
                        type="password"
                        placeholder="Enter password"
                        value={signupData.password}
                        onChange={(e) => setSignupData({ ...signupData, password: e.target.value })}
                        required
                        className="pl-10"
                        data-testid="signup-password-input"
                      />
                    </div>
                  </div>

                  <Button
                    type="submit"
                    className="w-full"
                    disabled={loading}
                    data-testid="signup-submit-btn"
                  >
                    {loading ? 'Creating Account...' : 'Sign Up'}
                  </Button>
                </form>
              ) : (
                <form onSubmit={handleVerifySignup} className="space-y-4">
                  <div className="text-center mb-4">
                    <Key className="w-12 h-12 mx-auto text-purple-600 mb-2" />
                    <p className="text-sm text-gray-600">
                      Enter the OTP sent to <strong>{signupTarget}</strong>
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="signup-otp">Verification OTP</Label>
                    <Input
                      id="signup-otp"
                      placeholder="Enter 6-digit OTP"
                      value={signupOTP}
                      onChange={(e) => setSignupOTP(e.target.value)}
                      required
                      maxLength={6}
                      className="text-center text-2xl tracking-widest"
                      data-testid="signup-otp-input"
                    />
                  </div>

                  <Button
                    type="submit"
                    className="w-full"
                    disabled={loading}
                    data-testid="verify-signup-btn"
                  >
                    {loading ? 'Verifying...' : 'Verify Account'}
                  </Button>
                </form>
              )
            ) : (
              !showLoginOTP ? (
                <form onSubmit={handleLoginPassword} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="login-identifier">Username / Email / Phone</Label>
                    <div className="relative">
                      <User className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="login-identifier"
                        placeholder="Enter your identifier"
                        value={loginData.identifier}
                        onChange={(e) => setLoginData({ ...loginData, identifier: e.target.value })}
                        required
                        className="pl-10"
                        data-testid="login-identifier-input"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="login-password">Password</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="login-password"
                        type="password"
                        placeholder="Enter password"
                        value={loginData.password}
                        onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                        required
                        className="pl-10"
                        data-testid="login-password-input"
                      />
                    </div>
                  </div>

                  <Button
                    type="submit"
                    className="w-full"
                    disabled={loading}
                    data-testid="login-submit-btn"
                  >
                    {loading ? 'Verifying...' : 'Continue'}
                  </Button>
                </form>
              ) : (
                <form onSubmit={handleVerifyLoginOTP} className="space-y-4">
                  <div className="text-center mb-4">
                    <Key className="w-12 h-12 mx-auto text-purple-600 mb-2" />
                    <p className="text-sm text-gray-600">
                      Enter the 2FA OTP sent to <strong>{loginTarget}</strong>
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="login-otp">2FA Code</Label>
                    <Input
                      id="login-otp"
                      placeholder="Enter 6-digit OTP"
                      value={loginOTP}
                      onChange={(e) => setLoginOTP(e.target.value)}
                      required
                      maxLength={6}
                      className="text-center text-2xl tracking-widest"
                      data-testid="login-otp-input"
                    />
                  </div>

                  <Button
                    type="submit"
                    className="w-full"
                    disabled={loading}
                    data-testid="verify-login-btn"
                  >
                    {loading ? 'Verifying...' : 'Login'}
                  </Button>
                </form>
              )
            )}
          </CardContent>
        </Card>

        <p className="text-center text-purple-100 text-sm mt-6">
          Secured with 2FA • Password + OTP Authentication
        </p>
      </div>
    </div>
  );
};

export default Auth;
