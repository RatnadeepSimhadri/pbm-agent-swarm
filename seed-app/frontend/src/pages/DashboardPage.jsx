import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useApi } from '../hooks/useApi';

export function DashboardPage() {
  const { member } = useAuth();
  const { get } = useApi();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    get('/api/members/me')
      .then(setProfile)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [get]);

  if (loading) {
    return <LoadingSkeleton />;
  }

  const firstName = profile?.first_name || member?.name?.split(' ')[0] || 'Member';

  return (
    <div className="space-y-6">
      {/* Greeting */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">
          Welcome back, {firstName}
        </h1>
        <p className="text-slate-500 mt-1">Here's a summary of your pharmacy benefits</p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Plan card */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-primary-50 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div>
              <p className="text-sm text-slate-500">Current Plan</p>
              <p className="text-lg font-semibold text-slate-900">{profile?.plan?.name}</p>
            </div>
          </div>
          <p className="text-sm text-slate-500 leading-relaxed">{profile?.plan?.description}</p>
          <Link
            to="/plan"
            className="inline-flex items-center gap-1 text-sm text-primary-600 hover:text-primary-800 font-medium mt-4 transition-colors"
          >
            View plan details
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </Link>
        </div>

        {/* Member info card */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-accent-50 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-accent-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            <div>
              <p className="text-sm text-slate-500">Member</p>
              <p className="text-lg font-semibold text-slate-900">{profile?.full_name}</p>
            </div>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-500">Email</span>
              <span className="text-slate-700">{profile?.email}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Date of Birth</span>
              <span className="text-slate-700">{formatDate(profile?.date_of_birth)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Member ID</span>
              <span className="text-slate-700 font-mono">PBM-{String(profile?.id).padStart(6, '0')}</span>
            </div>
          </div>
        </div>

        {/* Quick actions card */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-amber-50 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <p className="text-sm text-slate-500">Quick Actions</p>
              <p className="text-lg font-semibold text-slate-900">Get Started</p>
            </div>
          </div>
          <div className="space-y-2">
            <Link
              to="/medications"
              className="flex items-center gap-2 text-sm text-slate-600 hover:text-primary-700 py-1.5 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              Search medications
            </Link>
            <Link
              to="/plan"
              className="flex items-center gap-2 text-sm text-slate-600 hover:text-primary-700 py-1.5 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              View formulary tiers
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  return new Date(dateStr + 'T00:00:00').toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-8 bg-slate-200 rounded w-64" />
      <div className="h-4 bg-slate-200 rounded w-48" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white rounded-xl border border-slate-200 p-6 h-48" />
        ))}
      </div>
    </div>
  );
}
