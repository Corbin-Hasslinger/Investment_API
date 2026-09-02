import { Routes } from '@angular/router';

export const routes: Routes = [
    {
    path: '',
    loadComponent: () =>
      import('./features/dashboard/dashboard-page/dashboard-page')
        .then(m => m.DashboardPage),
  },
  {
    path: 'portfolios',
    loadComponent: () =>
      import('./features/portfolios/portfolio-list-page/portfolio-list-page')
        .then(m => m.PortfolioListPage),
  },
  {
    path: 'portfolios/:portfolioId',
    loadComponent: () =>
      import('./features/portfolios/portfolio-detail-page/portfolio-detail-page')
        .then(m => m.PortfolioDetailPage),
  },
  {
    path: 'research',
    loadComponent: () =>
      import('./features/research/research-search-page/research-search-page')
        .then(m => m.ResearchSearchPage),
  },
  {
    path: 'research/:symbol',
    loadComponent: () =>
      import('./features/research/research-detail-page/research-detail-page')
        .then(m => m.ResearchDetailPage),
  },
  {
    path: 'screener',
    loadComponent: () =>
      import('./features/screener/screener-page/screener-page')
        .then(m => m.ScreenerPage),
  },
  {
    path: '**',
    redirectTo: '',
  },
];
