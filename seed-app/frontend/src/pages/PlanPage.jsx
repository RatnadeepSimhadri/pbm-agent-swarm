import { useEffect, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useApi } from '../hooks/useApi';

const TIER_NAMES = {
  1: 'Preferred Generic',
  2: 'Non-Preferred Generic',
  3: 'Preferred Brand',
  4: 'Specialty',
};

const TIER_COLORS = {
  1: { bg: 'bg-emerald-50', text: 'text-emerald-700', badge: 'bg-emerald-100 text-emerald-800' },
  2: { bg: 'bg-blue-50', text: 'text-blue-700', badge: 'bg-blue-100 text-blue-800' },
  3: { bg: 'bg-amber-50', text: 'text-amber-700', badge: 'bg-amber-100 text-amber-800' },
  4: { bg: 'bg-red-50', text: 'text-red-700', badge: 'bg-red-100 text-red-800' },
};

export function PlanPage() {
  const { get } = useApi();
  const [profile, setProfile] = useState(null);
  const [formulary, setFormulary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      get('/api/members/me'),
      get('/api/members/me').then((m) => get(`/api/formulary/${m.plan_id}`)),
    ])
      .then(([memberData, formularyData]) => {
        setProfile(memberData);
        setFormulary(formularyData);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [get]);

  if (loading) {
    return <div className="animate-pulse space-y-4"><div className="h-8 bg-slate-200 rounded w-48" /><div className="h-64 bg-slate-200 rounded" /></div>;
  }

  // Group drugs by tier
  const tiers = {};
  formulary?.drugs?.forEach((drug) => {
    if (!tiers[drug.tier]) {
      tiers[drug.tier] = { drugs: [], copay: drug.copay_amount };
    }
    tiers[drug.tier].drugs.push(drug);
  });

  return (
    <div className="space-y-6">
      {/* Plan overview */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">{profile?.plan?.name}</h2>
            <p className="text-slate-500 mt-1">{profile?.plan?.description}</p>
          </div>
          <span className="px-3 py-1 bg-primary-50 text-primary-700 rounded-full text-sm font-medium">
            Active
          </span>
        </div>
      </div>

      {/* Tier breakdown */}
      <div>
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Formulary Tier Structure</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((tier) => {
            const colors = TIER_COLORS[tier];
            const tierData = tiers[tier];
            return (
              <div key={tier} className={`rounded-xl border border-slate-200 p-5 shadow-sm ${colors.bg}`}>
                <div className="flex items-center justify-between mb-3">
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${colors.badge}`}>
                    Tier {tier}
                  </span>
                  <span className={`text-2xl font-bold ${colors.text}`}>
                    ${tierData?.copay?.toFixed(0) || '—'}
                  </span>
                </div>
                <p className="text-sm font-medium text-slate-700">{TIER_NAMES[tier]}</p>
                <p className="text-xs text-slate-500 mt-1">
                  {tierData?.drugs?.length || 0} medications
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Formulary drug list by tier */}
      <div>
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Covered Medications</h3>
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">Medication</th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">Tier</th>
                <th className="text-right px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">Copay</th>
                <th className="text-center px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">Prior Auth</th>
                <th className="text-center px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">Step Therapy</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {formulary?.drugs?.map((drug) => {
                const colors = TIER_COLORS[drug.tier];
                return (
                  <tr key={drug.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-3">
                      <p className="text-sm font-medium text-slate-900">{drug.drug_name}</p>
                      {drug.generic_name && (
                        <p className="text-xs text-slate-400">Generic: {drug.generic_name}</p>
                      )}
                      {drug.brand_name && (
                        <p className="text-xs text-slate-400">Brand: {drug.brand_name}</p>
                      )}
                    </td>
                    <td className="px-6 py-3">
                      <span className={`inline-flex text-xs font-medium px-2 py-0.5 rounded-full ${colors.badge}`}>
                        Tier {drug.tier}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-right">
                      <span className="text-sm font-semibold text-slate-900">${drug.copay_amount.toFixed(2)}</span>
                    </td>
                    <td className="px-6 py-3 text-center">
                      {drug.prior_auth_required ? (
                        <span className="text-amber-500 text-sm">Required</span>
                      ) : (
                        <span className="text-slate-300 text-sm">No</span>
                      )}
                    </td>
                    <td className="px-6 py-3 text-center">
                      {drug.step_therapy_required ? (
                        <span className="text-amber-500 text-sm">Required</span>
                      ) : (
                        <span className="text-slate-300 text-sm">No</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
