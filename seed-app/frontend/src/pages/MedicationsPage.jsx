import { useCallback, useEffect, useState } from 'react';
import { useApi } from '../hooks/useApi';

const TIER_BADGES = {
  1: 'bg-emerald-100 text-emerald-800',
  2: 'bg-blue-100 text-blue-800',
  3: 'bg-amber-100 text-amber-800',
  4: 'bg-red-100 text-red-800',
};

const TIER_NAMES = {
  1: 'Preferred Generic',
  2: 'Non-Preferred Generic',
  3: 'Preferred Brand',
  4: 'Specialty',
};

export function MedicationsPage() {
  const { get } = useApi();
  const [drugs, setDrugs] = useState([]);
  const [total, setTotal] = useState(0);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [formularyMap, setFormularyMap] = useState({});

  // Load formulary data to show tier/copay for each drug
  useEffect(() => {
    get('/api/members/me')
      .then((member) => get(`/api/formulary/${member.plan_id}`))
      .then((formulary) => {
        const map = {};
        formulary.drugs.forEach((fd) => {
          map[fd.drug_id] = fd;
        });
        setFormularyMap(map);
      })
      .catch(console.error);
  }, [get]);

  const searchDrugs = useCallback((searchQuery) => {
    setLoading(true);
    const params = searchQuery ? `?q=${encodeURIComponent(searchQuery)}` : '';
    get(`/api/drugs${params}`)
      .then((data) => {
        setDrugs(data.drugs);
        setTotal(data.total);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [get]);

  useEffect(() => {
    searchDrugs(query);
  }, [searchDrugs, query]);

  return (
    <div className="space-y-6">
      {/* Search */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search medications by name..."
            className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors bg-white"
          />
        </div>
        <p className="text-sm text-slate-500">
          {total} medication{total !== 1 ? 's' : ''} found
        </p>
      </div>

      {/* Drug list */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {loading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="bg-white rounded-xl border border-slate-200 p-5 h-36 animate-pulse">
              <div className="h-4 bg-slate-200 rounded w-40 mb-2" />
              <div className="h-3 bg-slate-200 rounded w-24" />
            </div>
          ))
        ) : (
          drugs.map((drug) => {
            const formularyEntry = formularyMap[drug.id];
            return (
              <div key={drug.id} className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h3 className="text-sm font-semibold text-slate-900">{drug.name}</h3>
                    <p className="text-xs text-slate-500">{drug.strength} {drug.form}</p>
                  </div>
                  {formularyEntry && (
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${TIER_BADGES[formularyEntry.tier]}`}>
                      Tier {formularyEntry.tier}
                    </span>
                  )}
                </div>

                <p className="text-xs text-slate-400 mb-3 line-clamp-2">{drug.description}</p>

                <div className="flex items-center justify-between pt-3 border-t border-slate-100">
                  <div className="text-xs text-slate-500">
                    {drug.generic_name && <span>Generic: {drug.generic_name}</span>}
                    {drug.brand_name && <span>Brand: {drug.brand_name}</span>}
                    {!drug.generic_name && !drug.brand_name && <span>{drug.manufacturer}</span>}
                  </div>
                  {formularyEntry && (
                    <div className="text-right">
                      <p className="text-lg font-bold text-slate-900">${formularyEntry.copay_amount.toFixed(0)}</p>
                      <p className="text-xs text-slate-400">copay</p>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
