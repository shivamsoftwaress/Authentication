import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { authAPI } from '../services/api';
import { Button } from '../components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { User, Mail, Phone, Shield, LogOut, CheckCircle, Calendar } from 'lucide-react';

const CustomerDashboard = () => {
  const navigate = useNavigate();
  const { user, accessToken, refreshToken, logout } = useAuth();

  useEffect(() => {
    if (!user || user.role !== 'customer') {
      navigate('/');
    }
  }, [user, navigate]);

  const handleLogout = async () => {
    try {
      await authAPI.logout({ refresh_token: refreshToken }, accessToken);
      logout();
      navigate('/');
      toast.success('Logged out successfully');
    } catch (error) {
      logout();
      navigate('/');
    }
  };

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-700 rounded-xl flex items-center justify-center">
                <User className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Customer Dashboard</h1>
                <p className="text-sm text-gray-500">Welcome, {user.username}</p>
              </div>
            </div>
            <Button
              onClick={handleLogout}
              variant="outline"
              data-testid="customer-logout-btn"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Card */}
        <Card className="mb-8 border-0 shadow-lg bg-gradient-to-br from-blue-500 to-purple-600 text-white">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-2xl font-bold mb-2">Welcome back!</h2>
                <p className="text-blue-100">
                  Your account is secure and verified with 2FA authentication.
                </p>
              </div>
              <Shield className="w-16 h-16 text-white opacity-30" />
            </div>
          </CardContent>
        </Card>

        {/* Profile Information */}
        <Card className="shadow-lg border-0">
          <CardHeader>
            <CardTitle>Profile Information</CardTitle>
            <CardDescription>Your account details and verification status</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Username */}
            <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                <User className="w-6 h-6 text-blue-600" />
              </div>
              <div className="flex-1">
                <p className="text-sm text-gray-500">Username</p>
                <p className="font-semibold text-gray-900">{user.username}</p>
              </div>
            </div>

            {/* Email */}
            {user.email && (
              <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg">
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                  <Mail className="w-6 h-6 text-green-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm text-gray-500">Email</p>
                  <p className="font-semibold text-gray-900">{user.email}</p>
                </div>
              </div>
            )}

            {/* Phone */}
            {user.phone && (
              <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg">
                <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                  <Phone className="w-6 h-6 text-purple-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm text-gray-500">Phone</p>
                  <p className="font-semibold text-gray-900">{user.phone}</p>
                </div>
              </div>
            )}

            {/* Role */}
            <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg">
              <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
                <Shield className="w-6 h-6 text-orange-600" />
              </div>
              <div className="flex-1">
                <p className="text-sm text-gray-500">Role</p>
                <Badge className="mt-1">{user.role}</Badge>
              </div>
            </div>

            {/* Account Status */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <span className="font-medium text-green-900">Account Status</span>
                </div>
                <p className="text-sm text-green-700 mt-1">
                  {user.is_active ? 'Active' : 'Inactive'}
                </p>
              </div>

              <div className={`p-4 border rounded-lg ${user.is_verified ? 'bg-blue-50 border-blue-200' : 'bg-yellow-50 border-yellow-200'}`}>
                <div className="flex items-center space-x-2">
                  <CheckCircle className={`w-5 h-5 ${user.is_verified ? 'text-blue-600' : 'text-yellow-600'}`} />
                  <span className={`font-medium ${user.is_verified ? 'text-blue-900' : 'text-yellow-900'}`}>
                    Verification Status
                  </span>
                </div>
                <p className={`text-sm mt-1 ${user.is_verified ? 'text-blue-700' : 'text-yellow-700'}`}>
                  {user.is_verified ? 'Verified' : 'Pending Verification'}
                </p>
              </div>
            </div>

            {/* Created At */}
            {user.created_at && (
              <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg">
                <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center">
                  <Calendar className="w-6 h-6 text-gray-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm text-gray-500">Member Since</p>
                  <p className="font-semibold text-gray-900">
                    {new Date(user.created_at).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Security Info */}
        <Card className="mt-8 shadow-lg border-0 bg-gradient-to-r from-green-50 to-emerald-50 border-green-200">
          <CardContent className="pt-6">
            <div className="flex items-start space-x-4">
              <div className="w-12 h-12 bg-green-200 rounded-full flex items-center justify-center flex-shrink-0">
                <Shield className="w-6 h-6 text-green-700" />
              </div>
              <div>
                <h3 className="font-semibold text-green-900 mb-1">Protected by 2FA</h3>
                <p className="text-sm text-green-700">
                  Your account is secured with Two-Factor Authentication. Every login requires 
                  both your password and an OTP verification code.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

export default CustomerDashboard;