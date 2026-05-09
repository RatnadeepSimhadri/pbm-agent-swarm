import { useLocation } from 'react-router-dom';

const pageTitles = {
  '/': 'Dashboard',
  '/plan': 'My Plan',
  '/medications': 'Medications',
};

export function Header() {
  const location = useLocation();
  const title = pageTitles[location.pathname] || 'Dashboard';

  return (
    <header className="bg-white border-b border-slate-200 px-8 py-4">
      <h2 className="text-xl font-semibold text-slate-800">{title}</h2>
    </header>
  );
}
