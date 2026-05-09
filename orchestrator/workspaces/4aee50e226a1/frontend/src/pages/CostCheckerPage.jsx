import { useCallback, useEffect, useState } from 'react';
import { useApi } from '../hooks/useApi';

const TIER_BADGES = {
  1: 'bg-emerald-100 text-emerald-800',
  2: 'bg-blue-100 text-blue-800',
  3: 'bg-amber-100 text-amber-800',
  4: 'bg-red-100 text-red-800',
};

export function CostCheckerPage() {
  const { get } = useApi();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [memberPlan, setMemberPlan] = useState('');

  const search = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const data = await get(`/api/cost-estimate?drug_name=${encodeURIComponent(query)}`);
      setResults(data.results);
      setMemberPlan(data.member_plan);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [get, query]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Drug Cost Checker</h1>
        <p className="text-slate-500 mt-1">Estimate your copay before filling a prescription</p>
      </div>

      <div className="flex gap-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && search()}
          placeholder="Enter medication name..."
          className="flex-1 max-w-md px-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500"
        />
        <button
          onClick={search}
          disabled={loading || !query.trim()}
          className="px-6 py-2.5 bg-primary-700 text-white rounded-lg text-sm font-medium hover:bg-primary-800 disabled:opacity-50"
        >
          {loading ? 'Searching...' : 'Check Cost'}
        </button>
      </div>

      {results && (
        <div>
          <p className="text-sm text-slate-500 mb-4">
            {results.length} result(s) for your {memberPlan}
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {results.map((r) => (
              <div key={r.drug_id} className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="font-semibold text-slate-900">{r.drug_name}</h3>
                    <p className="text-xs text-slate-500">{r.strength} {r.form}</p>
                  </div>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${TIER_BADGES[r.tier]}`}>
                    {r.tier_name}
                  </span>
                </div>
                <div className="text-3xl font-bold text-primary-700 mb-3">${r.copay_amount.toFixed(2)}</div>
                <div className="space-y-1 text-xs text-slate-500">
                  {r.prior_auth_required && <p className="text-amber-600">Prior authorization required</p>}
                  {r.step_therapy_required && <p className="text-amber-600">Step therapy required</p>}
                  {r.quantity_limit && <p>Quantity limit: {r.quantity_limit} per fill</p>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
