# BeanBay Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a React SPA frontend for the BeanBay FastAPI REST API — full CRUD for all entities, stats dashboard, dual theme, mobile-first responsive layout.

**Architecture:** Feature-based modules (`features/<domain>/`) sharing a common component library and API layer. TypeScript types generated from OpenAPI spec. TanStack Query for server state, React Router for navigation, MUI for components.

**Tech Stack:** React 19, Vite 6, TypeScript 5.7, MUI 6, MUI X DataGrid 7, Axios, TanStack Query 5, React Router 7, Recharts 2, openapi-typescript 7

**Spec:** `docs/superpowers/specs/2026-03-21-beanbay-frontend-design.md`

---

## File Map

```
frontend/
├── package.json                           # Dependencies + scripts
├── vite.config.ts                         # Dev server proxy, path aliases
├── tsconfig.json                          # TypeScript config
├── tsconfig.node.json                     # Node-specific TS config for Vite
├── index.html                             # SPA entry point (loads Google Fonts)
├── .eslintrc.cjs                          # ESLint config
├── .prettierrc                            # Prettier config
├── scripts/
│   └── generate-types.sh                  # OpenAPI → TypeScript type generation
└── src/
    ├── main.tsx                           # React root + all providers
    ├── App.tsx                            # Router definition + route→page mapping
    ├── vite-env.d.ts                      # Vite type declarations
    ├── api/
    │   ├── client.ts                      # Axios instance, baseURL, error interceptor
    │   └── types.ts                       # Generated types (from openapi-typescript)
    ├── theme/
    │   ├── common.ts                      # Shared typography, shape, component overrides
    │   ├── espressoDark.ts                # Dark palette
    │   ├── craftLight.ts                  # Light palette
    │   └── ThemeContext.tsx               # Theme toggle context + localStorage
    ├── layouts/
    │   └── AppLayout.tsx                  # Sidebar + AppBar + FAB + content outlet
    ├── components/
    │   ├── NotificationProvider.tsx        # Snackbar context for toast notifications
    │   ├── PageHeader.tsx                 # Title + breadcrumbs + actions
    │   ├── ConfirmDialog.tsx              # Retire/delete confirmation
    │   ├── DataTable.tsx                  # MUI DataGrid wrapper
    │   ├── AutocompleteCreate.tsx         # FK/M2M picker + inline create
    │   ├── FlavorTagSelect.tsx            # Multi-select flavor tags
    │   ├── StatsCard.tsx                  # Dashboard metric card
    │   ├── TasteRadar.tsx                 # Recharts radar chart
    │   └── EmptyState.tsx                 # No-data call-to-action
    ├── utils/
    │   └── pagination.ts                  # usePaginationParams hook
    ├── features/
    │   ├── people/
    │   │   ├── PeoplePage.tsx
    │   │   ├── PersonFormDialog.tsx
    │   │   └── hooks.ts
    │   ├── settings/
    │   │   ├── LookupsPage.tsx
    │   │   ├── LookupTab.tsx
    │   │   └── hooks.ts
    │   ├── beans/
    │   │   ├── pages/
    │   │   │   ├── BeansListPage.tsx
    │   │   │   └── BeanDetailPage.tsx
    │   │   ├── components/
    │   │   │   ├── BeanFormDialog.tsx
    │   │   │   └── BagFormDialog.tsx
    │   │   └── hooks.ts
    │   ├── equipment/
    │   │   ├── pages/
    │   │   │   ├── PapersPage.tsx
    │   │   │   ├── WatersPage.tsx
    │   │   │   ├── GrindersPage.tsx
    │   │   │   └── BrewersPage.tsx
    │   │   ├── components/
    │   │   │   ├── PaperFormDialog.tsx
    │   │   │   ├── WaterFormDialog.tsx
    │   │   │   ├── GrinderFormDialog.tsx
    │   │   │   └── BrewerFormDialog.tsx
    │   │   └── hooks.ts
    │   ├── brew-setups/
    │   │   ├── BrewSetupsPage.tsx
    │   │   ├── BrewSetupFormDialog.tsx
    │   │   └── hooks.ts
    │   ├── brews/
    │   │   ├── pages/
    │   │   │   ├── BrewsListPage.tsx
    │   │   │   └── BrewDetailPage.tsx
    │   │   ├── components/
    │   │   │   ├── BrewWizard.tsx
    │   │   │   ├── BrewStepSetup.tsx
    │   │   │   ├── BrewStepParams.tsx
    │   │   │   └── BrewStepTaste.tsx
    │   │   └── hooks.ts
    │   ├── cuppings/
    │   │   ├── pages/
    │   │   │   ├── CuppingsListPage.tsx
    │   │   │   └── CuppingDetailPage.tsx
    │   │   ├── components/
    │   │   │   └── CuppingFormDialog.tsx
    │   │   └── hooks.ts
    │   ├── ratings/
    │   │   ├── RatingDetailPage.tsx
    │   │   ├── RatingFormDialog.tsx
    │   │   └── hooks.ts
    │   ├── bags/
    │   │   ├── BagsListPage.tsx
    │   │   └── hooks.ts
    │   └── dashboard/
    │       ├── DashboardPage.tsx
    │       └── hooks.ts
```

---

### Task 1: Scaffold Vite Project

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/index.html`
- Create: `frontend/.eslintrc.cjs`
- Create: `frontend/.prettierrc`
- Create: `frontend/src/vite-env.d.ts`

- [ ] **Step 1: Create frontend directory and initialize Vite React-TS project**

```bash
cd /Users/fzills/tools/BeanBay
npm create vite@latest frontend -- --template react-ts
```

- [ ] **Step 2: Install all dependencies**

```bash
cd /Users/fzills/tools/BeanBay/frontend
npm install @mui/material @mui/icons-material @emotion/react @emotion/styled \
  @mui/x-data-grid axios @tanstack/react-query @tanstack/react-query-devtools \
  react-router recharts
npm install -D openapi-typescript @types/react @types/react-dom eslint prettier
```

- [ ] **Step 3: Configure vite.config.ts with proxy and path alias**

```typescript
// frontend/vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

- [ ] **Step 4: Update tsconfig.json with path alias**

Add to `compilerOptions`:

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": { "@/*": ["src/*"] }
  }
}
```

- [ ] **Step 5: Configure index.html with Google Fonts**

```html
<!-- frontend/index.html -->
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>BeanBay</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Serif+Display&display=swap" rel="stylesheet" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 6: Add ESLint + Prettier configs**

```javascript
// frontend/.eslintrc.cjs
module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  parser: '@typescript-eslint/parser',
  rules: {
    '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
  },
};
```

```json
// frontend/.prettierrc
{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 100
}
```

- [ ] **Step 7: Remove Vite boilerplate files**

Delete `src/App.css`, `src/index.css`, `src/assets/`, and the default `src/App.tsx` content. Keep the files we'll overwrite in later tasks.

- [ ] **Step 8: Verify dev server starts**

```bash
cd /Users/fzills/tools/BeanBay/frontend && npm run dev
```

Expected: Vite dev server starts on `http://localhost:5173`

- [ ] **Step 9: Commit**

```bash
git add frontend/
git commit -m "feat(frontend): scaffold Vite React-TS project with dependencies"
```

---

### Task 2: Generate TypeScript Types from OpenAPI

**Files:**
- Create: `frontend/scripts/generate-types.sh`
- Create: `frontend/src/api/types.ts` (generated)

- [ ] **Step 1: Create the type generation script**

```bash
#!/usr/bin/env bash
# frontend/scripts/generate-types.sh
set -euo pipefail

API_URL="${BEANBAY_API_URL:-http://localhost:8000}"
OUT="$(dirname "$0")/../src/api/types.ts"

echo "Fetching OpenAPI spec from ${API_URL}/openapi.json..."
curl -sf "${API_URL}/openapi.json" | npx openapi-typescript /dev/stdin -o "$OUT"
echo "Types written to ${OUT}"
```

```bash
chmod +x frontend/scripts/generate-types.sh
```

- [ ] **Step 2: Add npm script to package.json**

Add to `frontend/package.json` scripts:

```json
{
  "scripts": {
    "generate-types": "./scripts/generate-types.sh"
  }
}
```

- [ ] **Step 3: Run type generation (requires backend running)**

```bash
cd /Users/fzills/tools/BeanBay/frontend && npm run generate-types
```

Expected: `src/api/types.ts` created with all schema types.

- [ ] **Step 4: Verify the generated file compiles**

```bash
cd /Users/fzills/tools/BeanBay/frontend && npx tsc --noEmit
```

Expected: No type errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/scripts/ frontend/src/api/types.ts frontend/package.json
git commit -m "feat(frontend): add OpenAPI type generation script and generated types"
```

---

### Task 3: Theme System

**Files:**
- Create: `frontend/src/theme/common.ts`
- Create: `frontend/src/theme/espressoDark.ts`
- Create: `frontend/src/theme/craftLight.ts`
- Create: `frontend/src/theme/ThemeContext.tsx`

- [ ] **Step 1: Create shared theme foundations**

```typescript
// frontend/src/theme/common.ts
import { type ThemeOptions } from '@mui/material/styles';

export const commonThemeOptions: ThemeOptions = {
  typography: {
    fontFamily: '"DM Sans", sans-serif',
    h1: { fontFamily: '"DM Serif Display", serif' },
    h2: { fontFamily: '"DM Serif Display", serif' },
    h3: { fontFamily: '"DM Serif Display", serif' },
    h4: { fontFamily: '"DM Serif Display", serif' },
    h5: { fontFamily: '"DM Sans", sans-serif', fontWeight: 600 },
    h6: { fontFamily: '"DM Sans", sans-serif', fontWeight: 600 },
    button: { textTransform: 'none', fontWeight: 600 },
  },
  shape: { borderRadius: 8 },
  components: {
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: { root: { minHeight: 40 } },
    },
    MuiTextField: {
      defaultProps: { size: 'small', fullWidth: true },
    },
    MuiDialog: {
      defaultProps: { fullWidth: true, maxWidth: 'sm' },
    },
  },
};
```

- [ ] **Step 2: Create Espresso Dark theme**

```typescript
// frontend/src/theme/espressoDark.ts
import { createTheme } from '@mui/material/styles';
import { commonThemeOptions } from './common';

export const espressoDark = createTheme({
  ...commonThemeOptions,
  palette: {
    mode: 'dark',
    primary: { main: '#c4956a' },
    secondary: { main: '#d4a574' },
    background: { default: '#1a1210', paper: '#2d1f1a' },
    text: { primary: '#e8dcc8', secondary: '#a89880' },
    error: { main: '#d4756a' },
    warning: { main: '#d4a56a' },
    success: { main: '#7ab57a' },
    divider: 'rgba(196,149,106,0.15)',
  },
});
```

- [ ] **Step 3: Create Craft Light theme**

```typescript
// frontend/src/theme/craftLight.ts
import { createTheme } from '@mui/material/styles';
import { commonThemeOptions } from './common';

export const craftLight = createTheme({
  ...commonThemeOptions,
  palette: {
    mode: 'light',
    primary: { main: '#8b5e3c' },
    secondary: { main: '#6b4c2a' },
    background: { default: '#faf8f5', paper: '#ffffff' },
    text: { primary: '#3d2b22', secondary: '#7a6a5a' },
    error: { main: '#c0392b' },
    warning: { main: '#d4a56a' },
    success: { main: '#27ae60' },
    divider: '#e0d6ca',
  },
});
```

- [ ] **Step 4: Create ThemeContext with localStorage persistence**

```tsx
// frontend/src/theme/ThemeContext.tsx
import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';
import { ThemeProvider as MuiThemeProvider, CssBaseline } from '@mui/material';
import { espressoDark } from './espressoDark';
import { craftLight } from './craftLight';

type ThemeMode = 'dark' | 'light';

interface ThemeContextValue {
  mode: ThemeMode;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue>({
  mode: 'dark',
  toggleTheme: () => {},
});

export const useThemeMode = () => useContext(ThemeContext);

const STORAGE_KEY = 'beanbay-theme';

function getInitialMode(): ThemeMode {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === 'light' || stored === 'dark') return stored;
  return 'dark';
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<ThemeMode>(getInitialMode);

  const toggleTheme = () => {
    setMode((prev) => {
      const next = prev === 'dark' ? 'light' : 'dark';
      localStorage.setItem(STORAGE_KEY, next);
      return next;
    });
  };

  const theme = useMemo(() => (mode === 'dark' ? espressoDark : craftLight), [mode]);

  const value = useMemo(() => ({ mode, toggleTheme }), [mode]);

  return (
    <ThemeContext.Provider value={value}>
      <MuiThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  );
}
```

- [ ] **Step 5: Verify themes compile**

```bash
cd /Users/fzills/tools/BeanBay/frontend && npx tsc --noEmit
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/theme/
git commit -m "feat(frontend): add dual theme system (Espresso Dark + Craft Light)"
```

---

### Task 4: API Client + Notification Provider

**Files:**
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/components/NotificationProvider.tsx`

- [ ] **Step 1: Create Axios client with error interceptor**

```typescript
// frontend/src/api/client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
});

// Error details are handled by NotificationProvider via a global event
export const API_ERROR_EVENT = 'beanbay:api-error';

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ??
      (typeof error.response?.data === 'string' ? error.response.data : null) ??
      error.message ??
      'Something went wrong';

    window.dispatchEvent(
      new CustomEvent(API_ERROR_EVENT, {
        detail: { message, status: error.response?.status },
      }),
    );

    return Promise.reject(error);
  },
);

export default apiClient;
```

- [ ] **Step 2: Create NotificationProvider with Snackbar**

```tsx
// frontend/src/components/NotificationProvider.tsx
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react';
import { Alert, Snackbar, useMediaQuery, useTheme } from '@mui/material';
import { API_ERROR_EVENT } from '@/api/client';

interface Notification {
  id: number;
  message: string;
  severity: 'success' | 'error' | 'warning' | 'info';
  autoHide?: number;
}

interface NotificationContextValue {
  notify: (message: string, severity?: Notification['severity'], autoHide?: number) => void;
}

const NotificationContext = createContext<NotificationContextValue>({
  notify: () => {},
});

export const useNotification = () => useContext(NotificationContext);

let nextId = 0;

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const notify = useCallback(
    (message: string, severity: Notification['severity'] = 'success', autoHide = 3000) => {
      const id = nextId++;
      setNotifications((prev) => [...prev, { id, message, severity, autoHide }]);
    },
    [],
  );

  const handleClose = useCallback((id: number) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  // Listen for API errors
  useEffect(() => {
    const handler = (e: Event) => {
      const { message } = (e as CustomEvent).detail;
      notify(message, 'error', undefined);
    };
    window.addEventListener(API_ERROR_EVENT, handler);
    return () => window.removeEventListener(API_ERROR_EVENT, handler);
  }, [notify]);

  return (
    <NotificationContext.Provider value={{ notify }}>
      {children}
      {notifications.map((n) => (
        <Snackbar
          key={n.id}
          open
          autoHideDuration={n.severity === 'error' ? null : (n.autoHide ?? 3000)}
          onClose={() => handleClose(n.id)}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: isMobile ? 'center' : 'left',
          }}
        >
          <Alert severity={n.severity} onClose={() => handleClose(n.id)} variant="filled">
            {n.message}
          </Alert>
        </Snackbar>
      ))}
    </NotificationContext.Provider>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/client.ts frontend/src/components/NotificationProvider.tsx
git commit -m "feat(frontend): add Axios API client and notification provider"
```

---

### Task 5: App Entry + Providers + Routing Skeleton

**Files:**
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/layouts/AppLayout.tsx` (skeleton)
- Create: `frontend/src/utils/pagination.ts`

- [ ] **Step 1: Create main.tsx with all providers**

```tsx
// frontend/src/main.tsx
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { ThemeProvider } from '@/theme/ThemeContext';
import { NotificationProvider } from '@/components/NotificationProvider';
import App from '@/App';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      gcTime: 300_000,
      retry: 1,
    },
  },
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <NotificationProvider>
            <App />
          </NotificationProvider>
        </ThemeProvider>
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </BrowserRouter>
  </StrictMode>,
);
```

- [ ] **Step 2: Create pagination utilities**

```typescript
// frontend/src/utils/pagination.ts
import { useSearchParams } from 'react-router';
import { useCallback, useMemo } from 'react';
import type { GridPaginationModel, GridSortModel } from '@mui/x-data-grid';

export interface PaginationParams {
  offset: number;
  limit: number;
  sort_by: string;
  sort_dir: 'asc' | 'desc';
  q?: string;
  include_retired?: boolean;
}

const DEFAULT_LIMIT = 25;

export function usePaginationParams(defaultSortBy = 'created_at') {
  const [searchParams, setSearchParams] = useSearchParams();

  const params: PaginationParams = useMemo(() => ({
    offset: parseInt(searchParams.get('offset') ?? '0', 10),
    limit: parseInt(searchParams.get('limit') ?? String(DEFAULT_LIMIT), 10),
    sort_by: searchParams.get('sort_by') ?? defaultSortBy,
    sort_dir: (searchParams.get('sort_dir') as 'asc' | 'desc') ?? 'desc',
    q: searchParams.get('q') ?? undefined,
    include_retired: searchParams.get('include_retired') === 'true',
  }), [searchParams, defaultSortBy]);

  const paginationModel: GridPaginationModel = useMemo(() => ({
    page: Math.floor(params.offset / params.limit),
    pageSize: params.limit,
  }), [params.offset, params.limit]);

  const sortModel: GridSortModel = useMemo(() => {
    if (!params.sort_by) return [];
    return [{ field: params.sort_by, sort: params.sort_dir }];
  }, [params.sort_by, params.sort_dir]);

  const onPaginationModelChange = useCallback(
    (model: GridPaginationModel) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.set('offset', String(model.page * model.pageSize));
        next.set('limit', String(model.pageSize));
        return next;
      });
    },
    [setSearchParams],
  );

  const onSortModelChange = useCallback(
    (model: GridSortModel) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        if (model.length > 0) {
          next.set('sort_by', model[0].field);
          next.set('sort_dir', model[0].sort ?? 'asc');
        }
        next.set('offset', '0');
        return next;
      });
    },
    [setSearchParams],
  );

  const setSearch = useCallback(
    (q: string) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        if (q) next.set('q', q);
        else next.delete('q');
        next.set('offset', '0');
        return next;
      });
    },
    [setSearchParams],
  );

  const setIncludeRetired = useCallback(
    (include: boolean) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        if (include) next.set('include_retired', 'true');
        else next.delete('include_retired');
        next.set('offset', '0');
        return next;
      });
    },
    [setSearchParams],
  );

  return {
    params,
    paginationModel,
    sortModel,
    onPaginationModelChange,
    onSortModelChange,
    setSearch,
    setIncludeRetired,
  };
}
```

- [ ] **Step 3: Create App.tsx with full route map and stub pages**

```tsx
// frontend/src/App.tsx
import { Routes, Route } from 'react-router';
import { lazy, Suspense } from 'react';
import { CircularProgress, Box } from '@mui/material';
import AppLayout from '@/layouts/AppLayout';

// Lazy-load all page components
const DashboardPage = lazy(() => import('@/features/dashboard/DashboardPage'));
const BeansListPage = lazy(() => import('@/features/beans/pages/BeansListPage'));
const BeanDetailPage = lazy(() => import('@/features/beans/pages/BeanDetailPage'));
const BagsListPage = lazy(() => import('@/features/bags/BagsListPage'));
const BrewsListPage = lazy(() => import('@/features/brews/pages/BrewsListPage'));
const BrewWizard = lazy(() => import('@/features/brews/components/BrewWizard'));
const BrewDetailPage = lazy(() => import('@/features/brews/pages/BrewDetailPage'));
const GrindersPage = lazy(() => import('@/features/equipment/pages/GrindersPage'));
const BrewersPage = lazy(() => import('@/features/equipment/pages/BrewersPage'));
const PapersPage = lazy(() => import('@/features/equipment/pages/PapersPage'));
const WatersPage = lazy(() => import('@/features/equipment/pages/WatersPage'));
const BrewSetupsPage = lazy(() => import('@/features/brew-setups/BrewSetupsPage'));
const CuppingsListPage = lazy(() => import('@/features/cuppings/pages/CuppingsListPage'));
const CuppingDetailPage = lazy(() => import('@/features/cuppings/pages/CuppingDetailPage'));
const RatingDetailPage = lazy(() => import('@/features/ratings/RatingDetailPage'));
const PeoplePage = lazy(() => import('@/features/people/PeoplePage'));
const LookupsPage = lazy(() => import('@/features/settings/LookupsPage'));

const Loading = () => (
  <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
    <CircularProgress />
  </Box>
);

export default function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="beans" element={<BeansListPage />} />
          <Route path="beans/:beanId" element={<BeanDetailPage />} />
          <Route path="bags" element={<BagsListPage />} />
          <Route path="brews" element={<BrewsListPage />} />
          <Route path="brews/new" element={<BrewWizard />} />
          <Route path="brews/:brewId" element={<BrewDetailPage />} />
          <Route path="equipment/grinders" element={<GrindersPage />} />
          <Route path="equipment/brewers" element={<BrewersPage />} />
          <Route path="equipment/papers" element={<PapersPage />} />
          <Route path="equipment/waters" element={<WatersPage />} />
          <Route path="brew-setups" element={<BrewSetupsPage />} />
          <Route path="cuppings" element={<CuppingsListPage />} />
          <Route path="cuppings/:cuppingId" element={<CuppingDetailPage />} />
          <Route path="bean-ratings/:ratingId" element={<RatingDetailPage />} />
          <Route path="people" element={<PeoplePage />} />
          <Route path="settings/lookups" element={<LookupsPage />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
```

- [ ] **Step 4: Create AppLayout skeleton**

Create a minimal `AppLayout.tsx` that renders the `<Outlet />` so routing works. Full sidebar/appbar implementation comes in Task 6.

```tsx
// frontend/src/layouts/AppLayout.tsx
import { Outlet } from 'react-router';
import { Box } from '@mui/material';

export default function AppLayout() {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Outlet />
      </Box>
    </Box>
  );
}
```

- [ ] **Step 5: Create stub placeholder pages for all features**

Create a simple placeholder component for every lazy-loaded page. Each file should default-export a component showing the page name. Example pattern:

```tsx
// frontend/src/features/dashboard/DashboardPage.tsx
import { Typography } from '@mui/material';
export default function DashboardPage() {
  return <Typography variant="h4">Dashboard</Typography>;
}
```

Create this pattern for ALL pages listed in the App.tsx imports: `DashboardPage`, `BeansListPage`, `BeanDetailPage`, `BagsListPage`, `BrewsListPage`, `BrewWizard`, `BrewDetailPage`, `GrindersPage`, `BrewersPage`, `PapersPage`, `WatersPage`, `BrewSetupsPage`, `CuppingsListPage`, `CuppingDetailPage`, `RatingDetailPage`, `PeoplePage`, `LookupsPage`.

Create the necessary directory structure under `src/features/` to match the file map.

- [ ] **Step 6: Verify app loads and routes work**

```bash
cd /Users/fzills/tools/BeanBay/frontend && npm run dev
```

Navigate to `http://localhost:5173/` — should see "Dashboard". Navigate to `/beans` — should see "Beans". Verify all routes render their placeholder.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/
git commit -m "feat(frontend): add app entry, routing, pagination utils, and stub pages"
```

---

### Task 6: AppLayout — Sidebar, App Bar, FAB

**Files:**
- Modify: `frontend/src/layouts/AppLayout.tsx`

- [ ] **Step 1: Implement full AppLayout with sidebar, app bar, and FAB**

Replace the skeleton with the full implementation:

```tsx
// frontend/src/layouts/AppLayout.tsx
import { useState } from 'react';
import { Outlet, useNavigate, useLocation, Link as RouterLink } from 'react-router';
import {
  AppBar,
  Box,
  Drawer,
  Fab,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  ListSubheader,
  Toolbar,
  Tooltip,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import {
  Menu as MenuIcon,
  ChevronLeft as ChevronLeftIcon,
  Dashboard as DashboardIcon,
  LocalCafe as BeansIcon,
  Inventory2 as BagsIcon,
  Coffee as BrewsIcon,
  BlenderOutlined as GrindersIcon,
  CoffeeMaker as BrewersIcon,
  FilterAlt as PapersIcon,
  WaterDrop as WatersIcon,
  Tune as SetupsIcon,
  Star as CuppingsIcon,
  People as PeopleIcon,
  Settings as SettingsIcon,
  Add as AddIcon,
  LightMode as LightModeIcon,
  DarkMode as DarkModeIcon,
} from '@mui/icons-material';
import { useThemeMode } from '@/theme/ThemeContext';

const DRAWER_WIDTH = 240;
const DRAWER_COLLAPSED = 64;

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
}

const navGroups: { label: string; items: NavItem[] }[] = [
  {
    label: 'Core',
    items: [
      { label: 'Dashboard', path: '/', icon: <DashboardIcon /> },
      { label: 'Beans', path: '/beans', icon: <BeansIcon /> },
      { label: 'Bags', path: '/bags', icon: <BagsIcon /> },
      { label: 'Brews', path: '/brews', icon: <BrewsIcon /> },
    ],
  },
  {
    label: 'Equipment',
    items: [
      { label: 'Grinders', path: '/equipment/grinders', icon: <GrindersIcon /> },
      { label: 'Brewers', path: '/equipment/brewers', icon: <BrewersIcon /> },
      { label: 'Papers', path: '/equipment/papers', icon: <PapersIcon /> },
      { label: 'Waters', path: '/equipment/waters', icon: <WatersIcon /> },
      { label: 'Brew Setups', path: '/brew-setups', icon: <SetupsIcon /> },
    ],
  },
  {
    label: 'Evaluation',
    items: [{ label: 'Cuppings', path: '/cuppings', icon: <CuppingsIcon /> }],
  },
  {
    label: 'Manage',
    items: [
      { label: 'People', path: '/people', icon: <PeopleIcon /> },
      { label: 'Lookups', path: '/settings/lookups', icon: <SettingsIcon /> },
    ],
  },
];

export default function AppLayout() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { mode, toggleTheme } = useThemeMode();

  const drawerWidth = isMobile ? DRAWER_WIDTH : collapsed ? DRAWER_COLLAPSED : DRAWER_WIDTH;

  const drawerContent = (
    <Box sx={{ overflow: 'auto', mt: isMobile ? 0 : 8 }}>
      {!isMobile && (
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', p: 1 }}>
          <IconButton onClick={() => setCollapsed(!collapsed)} size="small">
            <ChevronLeftIcon
              sx={{ transform: collapsed ? 'rotate(180deg)' : 'none', transition: '0.2s' }}
            />
          </IconButton>
        </Box>
      )}
      {navGroups.map((group) => (
        <List
          key={group.label}
          subheader={
            !collapsed ? (
              <ListSubheader sx={{ bgcolor: 'transparent', lineHeight: '32px', fontSize: 11, letterSpacing: 1, textTransform: 'uppercase' }}>
                {group.label}
              </ListSubheader>
            ) : undefined
          }
        >
          {group.items.map((item) => {
            const isActive =
              item.path === '/'
                ? location.pathname === '/'
                : location.pathname.startsWith(item.path);
            return (
              <ListItemButton
                key={item.path}
                component={RouterLink}
                to={item.path}
                selected={isActive}
                onClick={() => isMobile && setMobileOpen(false)}
                sx={{ minHeight: 44, px: collapsed ? 2.5 : 2 }}
              >
                <ListItemIcon sx={{ minWidth: collapsed ? 0 : 40 }}>
                  {item.icon}
                </ListItemIcon>
                {!collapsed && <ListItemText primary={item.label} />}
              </ListItemButton>
            );
          })}
        </List>
      ))}
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <AppBar
        position="fixed"
        color="default"
        elevation={0}
        sx={{
          zIndex: theme.zIndex.drawer + 1,
          borderBottom: 1,
          borderColor: 'divider',
          bgcolor: 'background.paper',
        }}
      >
        <Toolbar>
          {isMobile && (
            <IconButton edge="start" onClick={() => setMobileOpen(!mobileOpen)} sx={{ mr: 1 }}>
              <MenuIcon />
            </IconButton>
          )}
          <Typography
            variant="h6"
            noWrap
            component={RouterLink}
            to="/"
            sx={{ flexGrow: 1, textDecoration: 'none', color: 'text.primary', fontFamily: '"DM Serif Display", serif' }}
          >
            BeanBay
          </Typography>
          <Tooltip title={mode === 'dark' ? 'Switch to light' : 'Switch to dark'}>
            <IconButton onClick={toggleTheme}>
              {mode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>

      {isMobile ? (
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{ '& .MuiDrawer-paper': { width: DRAWER_WIDTH } }}
        >
          {drawerContent}
        </Drawer>
      ) : (
        <Drawer
          variant="permanent"
          sx={{
            width: drawerWidth,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: drawerWidth,
              transition: theme.transitions.create('width', { duration: 200 }),
              overflowX: 'hidden',
            },
          }}
        >
          {drawerContent}
        </Drawer>
      )}

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: { xs: 2, sm: 3 },
          mt: 8,
          width: { md: `calc(100% - ${drawerWidth}px)` },
        }}
      >
        <Outlet />
      </Box>

      <Fab
        color="primary"
        variant="extended"
        onClick={() => navigate('/brews/new')}
        sx={{
          position: 'fixed',
          bottom: { xs: 16, sm: 24 },
          right: { xs: 16, sm: 24 },
        }}
      >
        <AddIcon sx={{ mr: 1 }} />
        Log a Brew
      </Fab>
    </Box>
  );
}
```

- [ ] **Step 2: Verify layout renders on desktop and mobile**

```bash
cd /Users/fzills/tools/BeanBay/frontend && npm run dev
```

Check: sidebar visible on desktop, hamburger on mobile, theme toggle works, FAB visible, nav links route correctly.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/layouts/AppLayout.tsx
git commit -m "feat(frontend): implement AppLayout with sidebar, app bar, theme toggle, and FAB"
```

---

### Task 7: Shared Components — PageHeader, ConfirmDialog, EmptyState

**Files:**
- Create: `frontend/src/components/PageHeader.tsx`
- Create: `frontend/src/components/ConfirmDialog.tsx`
- Create: `frontend/src/components/EmptyState.tsx`

- [ ] **Step 1: Create PageHeader**

```tsx
// frontend/src/components/PageHeader.tsx
import { Box, Breadcrumbs, Button, Link, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router';
import type { ReactNode } from 'react';

interface BreadcrumbItem {
  label: string;
  to?: string;
}

interface PageHeaderProps {
  title: string;
  breadcrumbs?: BreadcrumbItem[];
  actions?: ReactNode;
}

export default function PageHeader({ title, breadcrumbs, actions }: PageHeaderProps) {
  return (
    <Box sx={{ mb: 3 }}>
      {breadcrumbs && breadcrumbs.length > 0 && (
        <Breadcrumbs sx={{ mb: 1 }}>
          {breadcrumbs.map((bc) =>
            bc.to ? (
              <Link key={bc.label} component={RouterLink} to={bc.to} underline="hover" color="inherit">
                {bc.label}
              </Link>
            ) : (
              <Typography key={bc.label} color="text.primary">
                {bc.label}
              </Typography>
            ),
          )}
        </Breadcrumbs>
      )}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 1 }}>
        <Typography variant="h4" component="h1">
          {title}
        </Typography>
        {actions && <Box sx={{ display: 'flex', gap: 1 }}>{actions}</Box>}
      </Box>
    </Box>
  );
}
```

- [ ] **Step 2: Create ConfirmDialog**

```tsx
// frontend/src/components/ConfirmDialog.tsx
import { Button, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle } from '@mui/material';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  variant?: 'retire' | 'delete';
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel,
  variant = 'retire',
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  return (
    <Dialog open={open} onClose={onCancel}>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <DialogContentText>{message}</DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel}>Cancel</Button>
        <Button onClick={onConfirm} color={variant === 'delete' ? 'error' : 'warning'} variant="contained">
          {confirmLabel ?? (variant === 'delete' ? 'Delete' : 'Retire')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
```

- [ ] **Step 3: Create EmptyState**

```tsx
// frontend/src/components/EmptyState.tsx
import { Box, Button, Typography } from '@mui/material';
import { type ReactNode } from 'react';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export default function EmptyState({ icon, title, description, actionLabel, onAction }: EmptyStateProps) {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', py: 8, gap: 2 }}>
      {icon && <Box sx={{ fontSize: 64, color: 'text.secondary', opacity: 0.5 }}>{icon}</Box>}
      <Typography variant="h6" color="text.secondary">{title}</Typography>
      {description && <Typography color="text.secondary">{description}</Typography>}
      {actionLabel && onAction && (
        <Button variant="contained" onClick={onAction} sx={{ mt: 1 }}>{actionLabel}</Button>
      )}
    </Box>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/PageHeader.tsx frontend/src/components/ConfirmDialog.tsx frontend/src/components/EmptyState.tsx
git commit -m "feat(frontend): add PageHeader, ConfirmDialog, and EmptyState components"
```

---

### Task 8: Shared Components — DataTable

**Files:**
- Create: `frontend/src/components/DataTable.tsx`

- [ ] **Step 1: Implement DataTable wrapper around MUI DataGrid**

```tsx
// frontend/src/components/DataTable.tsx
import { useCallback, useState } from 'react';
import {
  DataGrid,
  type GridColDef,
  type GridPaginationModel,
  type GridRowParams,
  type GridSortModel,
} from '@mui/x-data-grid';
import { Box, FormControlLabel, Switch, TextField, InputAdornment } from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router';
import EmptyState from '@/components/EmptyState';

interface DataTableProps<T extends { id: string }> {
  columns: GridColDef[];
  rows: T[];
  total: number;
  loading: boolean;
  paginationModel: GridPaginationModel;
  onPaginationModelChange: (model: GridPaginationModel) => void;
  sortModel: GridSortModel;
  onSortModelChange: (model: GridSortModel) => void;
  search?: string;
  onSearchChange?: (q: string) => void;
  includeRetired?: boolean;
  onIncludeRetiredChange?: (include: boolean) => void;
  detailPath?: (row: T) => string;
  emptyTitle?: string;
  emptyDescription?: string;
  emptyActionLabel?: string;
  onEmptyAction?: () => void;
}

export default function DataTable<T extends { id: string }>({
  columns,
  rows,
  total,
  loading,
  paginationModel,
  onPaginationModelChange,
  sortModel,
  onSortModelChange,
  search,
  onSearchChange,
  includeRetired,
  onIncludeRetiredChange,
  detailPath,
  emptyTitle = 'No items yet',
  emptyDescription,
  emptyActionLabel,
  onEmptyAction,
}: DataTableProps<T>) {
  const navigate = useNavigate();
  const [searchInput, setSearchInput] = useState(search ?? '');

  const handleSearchSubmit = useCallback(() => {
    onSearchChange?.(searchInput);
  }, [onSearchChange, searchInput]);

  const handleRowClick = useCallback(
    (params: GridRowParams<T>) => {
      if (detailPath) {
        navigate(detailPath(params.row));
      }
    },
    [navigate, detailPath],
  );

  if (!loading && rows.length === 0 && !search && !includeRetired) {
    return (
      <EmptyState
        title={emptyTitle}
        description={emptyDescription}
        actionLabel={emptyActionLabel}
        onAction={onEmptyAction}
      />
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        {onSearchChange && (
          <TextField
            size="small"
            placeholder="Search..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearchSubmit()}
            onBlur={handleSearchSubmit}
            slotProps={{
              input: {
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon fontSize="small" />
                  </InputAdornment>
                ),
              },
            }}
            sx={{ maxWidth: 300 }}
          />
        )}
        {onIncludeRetiredChange && (
          <FormControlLabel
            control={
              <Switch
                size="small"
                checked={includeRetired ?? false}
                onChange={(_, checked) => onIncludeRetiredChange(checked)}
              />
            }
            label="Show retired"
          />
        )}
      </Box>
      <DataGrid
        rows={rows}
        columns={columns}
        rowCount={total}
        loading={loading}
        paginationMode="server"
        paginationModel={paginationModel}
        onPaginationModelChange={onPaginationModelChange}
        pageSizeOptions={[10, 25, 50]}
        sortingMode="server"
        sortModel={sortModel}
        onSortModelChange={onSortModelChange}
        onRowClick={handleRowClick}
        disableRowSelectionOnClick
        autoHeight
        sx={{
          border: 0,
          cursor: detailPath ? 'pointer' : 'default',
          '& .MuiDataGrid-row:hover': detailPath ? { bgcolor: 'action.hover' } : {},
        }}
      />
    </Box>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/DataTable.tsx
git commit -m "feat(frontend): add DataTable component wrapping MUI DataGrid"
```

---

### Task 9: Shared Components — AutocompleteCreate + FlavorTagSelect

**Files:**
- Create: `frontend/src/components/AutocompleteCreate.tsx`
- Create: `frontend/src/components/FlavorTagSelect.tsx`

- [ ] **Step 1: Implement AutocompleteCreate**

```tsx
// frontend/src/components/AutocompleteCreate.tsx
import { useState, type ReactNode } from 'react';
import {
  Autocomplete,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  TextField,
  createFilterOptions,
  type AutocompleteRenderGetTagProps,
} from '@mui/material';
import { useQuery, useQueryClient } from '@tanstack/react-query';

interface OptionType {
  id: string;
  name: string;
  inputValue?: string;
}

const filter = createFilterOptions<OptionType>();

interface AutocompleteCreateProps<T extends OptionType> {
  label: string;
  queryKey: string[];
  fetchFn: (q: string) => Promise<{ items: T[] }>;
  value: T | T[] | null;
  onChange: (value: T | T[] | null) => void;
  multiple?: boolean;
  renderCreateForm?: (props: { onCreated: (item: T) => void; onCancel: () => void; initialName: string }) => ReactNode;
  error?: boolean;
  helperText?: string;
  required?: boolean;
}

export default function AutocompleteCreate<T extends OptionType>({
  label,
  queryKey,
  fetchFn,
  value,
  onChange,
  multiple = false,
  renderCreateForm,
  error,
  helperText,
  required,
}: AutocompleteCreateProps<T>) {
  const [inputValue, setInputValue] = useState('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [pendingName, setPendingName] = useState('');
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: [...queryKey, inputValue],
    queryFn: () => fetchFn(inputValue),
    staleTime: 30_000,
  });

  const options = (data?.items ?? []) as T[];

  const handleCreated = (item: T) => {
    queryClient.invalidateQueries({ queryKey });
    if (multiple) {
      const current = (value ?? []) as T[];
      onChange([...current, item]);
    } else {
      onChange(item);
    }
    setCreateDialogOpen(false);
  };

  return (
    <>
      <Autocomplete<T, boolean, false, true>
        multiple={multiple as boolean}
        freeSolo
        options={options}
        loading={isLoading}
        getOptionLabel={(option) => (typeof option === 'string' ? option : option.name)}
        isOptionEqualToValue={(option, val) => option.id === val.id}
        value={value as T & T[]}
        inputValue={inputValue}
        onInputChange={(_, newInput) => setInputValue(newInput)}
        onChange={(_, newValue) => {
          if (Array.isArray(newValue)) {
            const createItem = newValue.find(
              (v): v is T & { inputValue: string } =>
                typeof v !== 'string' && 'inputValue' in v && !!v.inputValue,
            );
            if (createItem && renderCreateForm) {
              setPendingName(createItem.inputValue);
              setCreateDialogOpen(true);
              return;
            }
            onChange(newValue.filter((v) => typeof v !== 'string') as T[]);
          } else if (newValue && typeof newValue !== 'string' && 'inputValue' in newValue && newValue.inputValue && renderCreateForm) {
            setPendingName(newValue.inputValue);
            setCreateDialogOpen(true);
          } else {
            onChange(typeof newValue === 'string' ? null : (newValue as T | null));
          }
        }}
        filterOptions={(opts, params) => {
          const filtered = filter(opts, params);
          if (renderCreateForm && params.inputValue !== '' && !opts.some((o) => o.name === params.inputValue)) {
            filtered.push({
              id: '',
              name: `+ Create "${params.inputValue}"`,
              inputValue: params.inputValue,
            } as T);
          }
          return filtered;
        }}
        renderInput={(params) => (
          <TextField {...params} label={label} error={error} helperText={helperText} required={required} />
        )}
        renderTags={
          multiple
            ? (tagValues: T[], getTagProps: AutocompleteRenderGetTagProps) =>
                tagValues.map((option, index) => {
                  const { key, ...rest } = getTagProps({ index });
                  return <Chip key={key} label={option.name} size="small" {...rest} />;
                })
            : undefined
        }
      />
      {renderCreateForm && (
        <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)}>
          <DialogTitle>Create {label}</DialogTitle>
          <DialogContent>
            {renderCreateForm({
              onCreated: handleCreated,
              onCancel: () => setCreateDialogOpen(false),
              initialName: pendingName,
            })}
          </DialogContent>
        </Dialog>
      )}
    </>
  );
}
```

- [ ] **Step 2: Implement FlavorTagSelect**

```tsx
// frontend/src/components/FlavorTagSelect.tsx
import AutocompleteCreate from '@/components/AutocompleteCreate';
import apiClient from '@/api/client';
import { Button, Stack, TextField } from '@mui/material';
import { useState } from 'react';
import { useNotification } from '@/components/NotificationProvider';

interface FlavorTag {
  id: string;
  name: string;
}

interface FlavorTagSelectProps {
  value: FlavorTag[];
  onChange: (tags: FlavorTag[]) => void;
  error?: boolean;
  helperText?: string;
}

function CreateFlavorTagForm({
  initialName,
  onCreated,
  onCancel,
}: {
  initialName: string;
  onCreated: (tag: FlavorTag) => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState(initialName);
  const { notify } = useNotification();

  const handleSubmit = async () => {
    const { data } = await apiClient.post<FlavorTag>('/flavor-tags', { name });
    notify('Flavor tag created');
    onCreated(data);
  };

  return (
    <Stack spacing={2} sx={{ pt: 1 }}>
      <TextField label="Name" value={name} onChange={(e) => setName(e.target.value)} required autoFocus />
      <Stack direction="row" spacing={1} justifyContent="flex-end">
        <Button onClick={onCancel}>Cancel</Button>
        <Button variant="contained" onClick={handleSubmit} disabled={!name.trim()}>
          Create
        </Button>
      </Stack>
    </Stack>
  );
}

export default function FlavorTagSelect({ value, onChange, error, helperText }: FlavorTagSelectProps) {
  return (
    <AutocompleteCreate<FlavorTag>
      label="Flavor Tags"
      queryKey={['flavor-tags']}
      fetchFn={async (q) => {
        const { data } = await apiClient.get('/flavor-tags', { params: { q, limit: 50 } });
        return data;
      }}
      value={value}
      onChange={(v) => onChange((v ?? []) as FlavorTag[])}
      multiple
      error={error}
      helperText={helperText}
      renderCreateForm={(props) => <CreateFlavorTagForm {...props} />}
    />
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/AutocompleteCreate.tsx frontend/src/components/FlavorTagSelect.tsx
git commit -m "feat(frontend): add AutocompleteCreate and FlavorTagSelect components"
```

---

### Task 10: Shared Components — StatsCard + TasteRadar

**Files:**
- Create: `frontend/src/components/StatsCard.tsx`
- Create: `frontend/src/components/TasteRadar.tsx`

- [ ] **Step 1: Implement StatsCard**

```tsx
// frontend/src/components/StatsCard.tsx
import { Card, CardContent, Skeleton, Typography, type SxProps } from '@mui/material';
import type { ReactNode } from 'react';

interface StatsCardProps {
  label: string;
  value: string | number | null | undefined;
  icon?: ReactNode;
  loading?: boolean;
  sx?: SxProps;
}

export default function StatsCard({ label, value, icon, loading, sx }: StatsCardProps) {
  return (
    <Card sx={{ minWidth: 140, ...sx }}>
      <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        {icon && <div style={{ fontSize: 32, opacity: 0.7 }}>{icon}</div>}
        <div>
          <Typography variant="body2" color="text.secondary">
            {label}
          </Typography>
          {loading ? (
            <Skeleton width={60} height={32} />
          ) : (
            <Typography variant="h5" component="div">
              {value ?? '—'}
            </Typography>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 2: Implement TasteRadar**

```tsx
// frontend/src/components/TasteRadar.tsx
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from 'recharts';
import { useTheme } from '@mui/material';

interface TasteDataPoint {
  axis: string;
  value: number | null;
}

interface TasteRadarProps {
  data: TasteDataPoint[];
  maxValue?: number;
  size?: number;
}

export default function TasteRadar({ data, maxValue = 10, size = 300 }: TasteRadarProps) {
  const theme = useTheme();

  const chartData = data.map((d) => ({
    axis: d.axis,
    value: d.value ?? 0,
  }));

  return (
    <ResponsiveContainer width="100%" height={size}>
      <RadarChart data={chartData}>
        <PolarGrid stroke={theme.palette.divider} />
        <PolarAngleAxis
          dataKey="axis"
          tick={{ fill: theme.palette.text.secondary, fontSize: 12 }}
        />
        <PolarRadiusAxis
          domain={[0, maxValue]}
          tick={{ fill: theme.palette.text.secondary, fontSize: 10 }}
          axisLine={false}
        />
        <Radar
          name="Taste"
          dataKey="value"
          stroke={theme.palette.primary.main}
          fill={theme.palette.primary.main}
          fillOpacity={0.3}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}

// Convenience helpers for converting API data to TasteDataPoint[]
export function brewTasteToRadar(taste: {
  acidity?: number | null;
  sweetness?: number | null;
  body?: number | null;
  bitterness?: number | null;
  balance?: number | null;
  aftertaste?: number | null;
}): TasteDataPoint[] {
  return [
    { axis: 'Acidity', value: taste.acidity ?? null },
    { axis: 'Sweetness', value: taste.sweetness ?? null },
    { axis: 'Body', value: taste.body ?? null },
    { axis: 'Bitterness', value: taste.bitterness ?? null },
    { axis: 'Balance', value: taste.balance ?? null },
    { axis: 'Aftertaste', value: taste.aftertaste ?? null },
  ];
}

export function beanTasteToRadar(taste: {
  acidity?: number | null;
  sweetness?: number | null;
  body?: number | null;
  complexity?: number | null;
  aroma?: number | null;
  clean_cup?: number | null;
}): TasteDataPoint[] {
  return [
    { axis: 'Acidity', value: taste.acidity ?? null },
    { axis: 'Sweetness', value: taste.sweetness ?? null },
    { axis: 'Body', value: taste.body ?? null },
    { axis: 'Complexity', value: taste.complexity ?? null },
    { axis: 'Aroma', value: taste.aroma ?? null },
    { axis: 'Clean Cup', value: taste.clean_cup ?? null },
  ];
}

export function cuppingToRadar(cupping: {
  dry_fragrance?: number | null;
  wet_aroma?: number | null;
  brightness?: number | null;
  flavor?: number | null;
  body?: number | null;
  finish?: number | null;
  sweetness?: number | null;
  clean_cup?: number | null;
  complexity?: number | null;
  uniformity?: number | null;
}): TasteDataPoint[] {
  return [
    { axis: 'Dry Fragrance', value: cupping.dry_fragrance ?? null },
    { axis: 'Wet Aroma', value: cupping.wet_aroma ?? null },
    { axis: 'Brightness', value: cupping.brightness ?? null },
    { axis: 'Flavor', value: cupping.flavor ?? null },
    { axis: 'Body', value: cupping.body ?? null },
    { axis: 'Finish', value: cupping.finish ?? null },
    { axis: 'Sweetness', value: cupping.sweetness ?? null },
    { axis: 'Clean Cup', value: cupping.clean_cup ?? null },
    { axis: 'Complexity', value: cupping.complexity ?? null },
    { axis: 'Uniformity', value: cupping.uniformity ?? null },
  ];
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/StatsCard.tsx frontend/src/components/TasteRadar.tsx
git commit -m "feat(frontend): add StatsCard and TasteRadar components"
```

---

### Task 11: People Feature (Pattern Establisher)

This is the simplest CRUD feature and establishes the hook + page pattern all other features follow.

**Files:**
- Modify: `frontend/src/features/people/PeoplePage.tsx`
- Create: `frontend/src/features/people/PersonFormDialog.tsx`
- Create: `frontend/src/features/people/hooks.ts`

- [ ] **Step 1: Create people hooks**

```typescript
// frontend/src/features/people/hooks.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/api/client';
import type { PaginationParams } from '@/utils/pagination';

export interface Person {
  id: string;
  name: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
  retired_at: string | null;
  is_retired: boolean;
}

interface PaginatedPeople {
  items: Person[];
  total: number;
  limit: number;
  offset: number;
}

export function usePeople(params: PaginationParams) {
  return useQuery<PaginatedPeople>({
    queryKey: ['people', params],
    queryFn: async () => {
      const { data } = await apiClient.get('/people', { params });
      return data;
    },
  });
}

export function useCreatePerson() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { name: string }) => {
      const { data } = await apiClient.post('/people', body);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['people'] }),
  });
}

export function useUpdatePerson() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...body }: { id: string; name?: string; is_default?: boolean }) => {
      const { data } = await apiClient.patch(`/people/${id}`, body);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['people'] }),
  });
}

export function useDeletePerson() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/people/${id}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['people'] }),
  });
}
```

- [ ] **Step 2: Create PersonFormDialog**

```tsx
// frontend/src/features/people/PersonFormDialog.tsx
import { useState, useEffect } from 'react';
import { Button, Dialog, DialogActions, DialogContent, DialogTitle, Stack, Switch, FormControlLabel, TextField } from '@mui/material';
import { useCreatePerson, useUpdatePerson, type Person } from './hooks';
import { useNotification } from '@/components/NotificationProvider';

interface PersonFormDialogProps {
  open: boolean;
  onClose: () => void;
  person?: Person | null;
}

export default function PersonFormDialog({ open, onClose, person }: PersonFormDialogProps) {
  const [name, setName] = useState('');
  const [isDefault, setIsDefault] = useState(false);
  const isEdit = !!person;
  const create = useCreatePerson();
  const update = useUpdatePerson();
  const { notify } = useNotification();

  useEffect(() => {
    if (person) {
      setName(person.name);
      setIsDefault(person.is_default);
    } else {
      setName('');
      setIsDefault(false);
    }
  }, [person, open]);

  const handleSubmit = async () => {
    if (isEdit) {
      await update.mutateAsync({ id: person!.id, name, is_default: isDefault });
      notify('Person updated');
    } else {
      await create.mutateAsync({ name });
      notify('Person created');
    }
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>{isEdit ? 'Edit Person' : 'Add Person'}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          <TextField label="Name" value={name} onChange={(e) => setName(e.target.value)} required autoFocus />
          {isEdit && (
            <FormControlLabel
              control={<Switch checked={isDefault} onChange={(_, c) => setIsDefault(c)} />}
              label="Default person"
            />
          )}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={handleSubmit} disabled={!name.trim()}>
          {isEdit ? 'Save' : 'Create'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
```

- [ ] **Step 3: Implement PeoplePage**

```tsx
// frontend/src/features/people/PeoplePage.tsx
import { useState } from 'react';
import { type GridColDef } from '@mui/x-data-grid';
import { Button, Chip } from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import PageHeader from '@/components/PageHeader';
import DataTable from '@/components/DataTable';
import ConfirmDialog from '@/components/ConfirmDialog';
import { usePaginationParams } from '@/utils/pagination';
import { usePeople, useDeletePerson, type Person } from './hooks';
import PersonFormDialog from './PersonFormDialog';
import { useNotification } from '@/components/NotificationProvider';

const columns: GridColDef[] = [
  { field: 'name', headerName: 'Name', flex: 1, minWidth: 150 },
  {
    field: 'is_default',
    headerName: 'Default',
    width: 100,
    renderCell: (params) =>
      params.value ? <Chip label="Default" size="small" color="primary" /> : null,
  },
];

export default function PeoplePage() {
  const { params, paginationModel, sortModel, onPaginationModelChange, onSortModelChange, setSearch, setIncludeRetired } =
    usePaginationParams('name');
  const { data, isLoading } = usePeople(params);
  const deletePerson = useDeletePerson();
  const { notify } = useNotification();

  const [formOpen, setFormOpen] = useState(false);
  const [editPerson, setEditPerson] = useState<Person | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Person | null>(null);

  const handleEdit = (person: Person) => {
    setEditPerson(person);
    setFormOpen(true);
  };

  const handleDelete = async () => {
    if (deleteTarget) {
      await deletePerson.mutateAsync(deleteTarget.id);
      notify('Person retired');
      setDeleteTarget(null);
    }
  };

  return (
    <>
      <PageHeader
        title="People"
        actions={
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => { setEditPerson(null); setFormOpen(true); }}>
            Add Person
          </Button>
        }
      />
      <DataTable<Person>
        columns={columns}
        rows={data?.items ?? []}
        total={data?.total ?? 0}
        loading={isLoading}
        paginationModel={paginationModel}
        onPaginationModelChange={onPaginationModelChange}
        sortModel={sortModel}
        onSortModelChange={onSortModelChange}
        search={params.q}
        onSearchChange={setSearch}
        includeRetired={params.include_retired}
        onIncludeRetiredChange={setIncludeRetired}
        emptyTitle="No people yet"
        emptyActionLabel="Add Person"
        onEmptyAction={() => { setEditPerson(null); setFormOpen(true); }}
      />
      <PersonFormDialog open={formOpen} onClose={() => setFormOpen(false)} person={editPerson} />
      <ConfirmDialog
        open={!!deleteTarget}
        title="Retire Person"
        message={`Retire "${deleteTarget?.name}"? This won't delete their brews or ratings.`}
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </>
  );
}
```

Note: The `handleEdit` function is ready for use — wire it from the DataGrid via a row action column or row click event as preferred. A simple approach is to add an actions column to `columns` or use the DataGrid `onRowClick` to open the edit dialog.

- [ ] **Step 4: Verify people CRUD works**

```bash
cd /Users/fzills/tools/BeanBay/frontend && npm run dev
```

Navigate to `/people`. Verify: list loads from API, "Add Person" opens form, creating a person shows success toast, editing works with is_default toggle.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/people/
git commit -m "feat(frontend): implement People feature with CRUD"
```

---

### Task 12: Lookups Feature (Tabbed Settings Page)

**Files:**
- Modify: `frontend/src/features/settings/LookupsPage.tsx`
- Create: `frontend/src/features/settings/LookupTab.tsx`
- Create: `frontend/src/features/settings/hooks.ts`

- [ ] **Step 1: Create generic lookup hooks factory**

```typescript
// frontend/src/features/settings/hooks.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/api/client';
import type { PaginationParams } from '@/utils/pagination';

export interface LookupItem {
  id: string;
  name: string;
  created_at: string;
  retired_at: string | null;
  is_retired: boolean;
  [key: string]: unknown;
}

export function createLookupHooks(endpoint: string) {
  const queryKey = [endpoint];

  return {
    useList: (params: PaginationParams) =>
      useQuery({
        queryKey: [...queryKey, params],
        queryFn: async () => {
          const { data } = await apiClient.get(`/${endpoint}`, { params });
          return data as { items: LookupItem[]; total: number };
        },
      }),
    useCreate: () => {
      const qc = useQueryClient();
      return useMutation({
        mutationFn: async (body: Record<string, unknown>) => {
          const { data } = await apiClient.post(`/${endpoint}`, body);
          return data;
        },
        onSuccess: () => qc.invalidateQueries({ queryKey }),
      });
    },
    useUpdate: () => {
      const qc = useQueryClient();
      return useMutation({
        mutationFn: async ({ id, ...body }: { id: string; [key: string]: unknown }) => {
          const { data } = await apiClient.patch(`/${endpoint}/${id}`, body);
          return data;
        },
        onSuccess: () => qc.invalidateQueries({ queryKey }),
      });
    },
    useDelete: () => {
      const qc = useQueryClient();
      return useMutation({
        mutationFn: async (id: string) => {
          await apiClient.delete(`/${endpoint}/${id}`);
        },
        onSuccess: () => qc.invalidateQueries({ queryKey }),
      });
    },
  };
}

// Pre-built hooks for each lookup type
export const flavorTagHooks = createLookupHooks('flavor-tags');
export const originHooks = createLookupHooks('origins');
export const roasterHooks = createLookupHooks('roasters');
export const processMethodHooks = createLookupHooks('process-methods');
export const beanVarietyHooks = createLookupHooks('bean-varieties');
export const brewMethodHooks = createLookupHooks('brew-methods');
export const stopModeHooks = createLookupHooks('stop-modes');
export const vendorHooks = createLookupHooks('vendors');
export const storageTypeHooks = createLookupHooks('storage-types');
```

- [ ] **Step 2: Create LookupTab — generic CRUD tab component**

```tsx
// frontend/src/features/settings/LookupTab.tsx
import { useState, useEffect } from 'react';
import { type GridColDef } from '@mui/x-data-grid';
import { Button, Dialog, DialogActions, DialogContent, DialogTitle, Stack, TextField } from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import DataTable from '@/components/DataTable';
import ConfirmDialog from '@/components/ConfirmDialog';
import { usePaginationParams } from '@/utils/pagination';
import { useNotification } from '@/components/NotificationProvider';
import type { LookupItem } from './hooks';

interface FieldConfig {
  name: string;
  label: string;
  required?: boolean;
  type?: 'text' | 'select';
  options?: string[];
}

interface LookupTabProps {
  hooks: ReturnType<typeof import('./hooks').createLookupHooks>;
  columns: GridColDef[];
  fields: FieldConfig[];
  entityName: string;
}

export default function LookupTab({ hooks, columns, fields, entityName }: LookupTabProps) {
  const { params, paginationModel, sortModel, onPaginationModelChange, onSortModelChange, setSearch, setIncludeRetired } =
    usePaginationParams('name');
  const { data, isLoading } = hooks.useList(params);
  const create = hooks.useCreate();
  const update = hooks.useUpdate();
  const del = hooks.useDelete();
  const { notify } = useNotification();

  const [formOpen, setFormOpen] = useState(false);
  const [editItem, setEditItem] = useState<LookupItem | null>(null);
  const [formValues, setFormValues] = useState<Record<string, string>>({});
  const [deleteTarget, setDeleteTarget] = useState<LookupItem | null>(null);

  useEffect(() => {
    if (editItem) {
      const values: Record<string, string> = {};
      fields.forEach((f) => { values[f.name] = String(editItem[f.name] ?? ''); });
      setFormValues(values);
    } else {
      const values: Record<string, string> = {};
      fields.forEach((f) => { values[f.name] = ''; });
      setFormValues(values);
    }
  }, [editItem, formOpen, fields]);

  const handleSubmit = async () => {
    const body: Record<string, unknown> = {};
    fields.forEach((f) => { body[f.name] = formValues[f.name] || null; });
    if (editItem) {
      await update.mutateAsync({ id: editItem.id, ...body });
      notify(`${entityName} updated`);
    } else {
      await create.mutateAsync(body);
      notify(`${entityName} created`);
    }
    setFormOpen(false);
    setEditItem(null);
  };

  const handleDelete = async () => {
    if (deleteTarget) {
      await del.mutateAsync(deleteTarget.id);
      notify(`${entityName} retired`);
      setDeleteTarget(null);
    }
  };

  return (
    <>
      <Button
        variant="outlined"
        startIcon={<AddIcon />}
        onClick={() => { setEditItem(null); setFormOpen(true); }}
        sx={{ mb: 2 }}
      >
        Add {entityName}
      </Button>
      <DataTable<LookupItem>
        columns={columns}
        rows={data?.items ?? []}
        total={data?.total ?? 0}
        loading={isLoading}
        paginationModel={paginationModel}
        onPaginationModelChange={onPaginationModelChange}
        sortModel={sortModel}
        onSortModelChange={onSortModelChange}
        search={params.q}
        onSearchChange={setSearch}
        includeRetired={params.include_retired}
        onIncludeRetiredChange={setIncludeRetired}
        emptyTitle={`No ${entityName.toLowerCase()}s yet`}
        emptyActionLabel={`Add ${entityName}`}
        onEmptyAction={() => { setEditItem(null); setFormOpen(true); }}
      />
      <Dialog open={formOpen} onClose={() => { setFormOpen(false); setEditItem(null); }}>
        <DialogTitle>{editItem ? `Edit ${entityName}` : `Add ${entityName}`}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ pt: 1 }}>
            {fields.map((f) => (
              <TextField
                key={f.name}
                label={f.label}
                value={formValues[f.name] ?? ''}
                onChange={(e) => setFormValues((prev) => ({ ...prev, [f.name]: e.target.value }))}
                required={f.required}
              />
            ))}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setFormOpen(false); setEditItem(null); }}>Cancel</Button>
          <Button variant="contained" onClick={handleSubmit} disabled={fields.some((f) => f.required && !formValues[f.name]?.trim())}>
            {editItem ? 'Save' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
      <ConfirmDialog
        open={!!deleteTarget}
        title={`Retire ${entityName}`}
        message={`Retire "${deleteTarget?.name}"?`}
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </>
  );
}
```

- [ ] **Step 3: Implement LookupsPage with all 9 tabs**

```tsx
// frontend/src/features/settings/LookupsPage.tsx
import { useState } from 'react';
import { Box, Tab, Tabs } from '@mui/material';
import PageHeader from '@/components/PageHeader';
import LookupTab from './LookupTab';
import {
  flavorTagHooks, originHooks, roasterHooks, processMethodHooks,
  beanVarietyHooks, brewMethodHooks, stopModeHooks, vendorHooks, storageTypeHooks,
} from './hooks';

const tabs = [
  {
    label: 'Flavor Tags', entityName: 'Flavor Tag', hooks: flavorTagHooks,
    columns: [{ field: 'name', headerName: 'Name', flex: 1 }],
    fields: [{ name: 'name', label: 'Name', required: true }],
  },
  {
    label: 'Origins', entityName: 'Origin', hooks: originHooks,
    columns: [
      { field: 'name', headerName: 'Name', flex: 1 },
      { field: 'country', headerName: 'Country', flex: 1 },
      { field: 'region', headerName: 'Region', flex: 1 },
    ],
    fields: [
      { name: 'name', label: 'Name', required: true },
      { name: 'country', label: 'Country' },
      { name: 'region', label: 'Region' },
    ],
  },
  {
    label: 'Roasters', entityName: 'Roaster', hooks: roasterHooks,
    columns: [{ field: 'name', headerName: 'Name', flex: 1 }],
    fields: [{ name: 'name', label: 'Name', required: true }],
  },
  {
    label: 'Process Methods', entityName: 'Process Method', hooks: processMethodHooks,
    columns: [
      { field: 'name', headerName: 'Name', flex: 1 },
      { field: 'category', headerName: 'Category', width: 150 },
    ],
    fields: [
      { name: 'name', label: 'Name', required: true },
      { name: 'category', label: 'Category' },
    ],
  },
  {
    label: 'Bean Varieties', entityName: 'Bean Variety', hooks: beanVarietyHooks,
    columns: [
      { field: 'name', headerName: 'Name', flex: 1 },
      { field: 'species', headerName: 'Species', width: 150 },
    ],
    fields: [
      { name: 'name', label: 'Name', required: true },
      { name: 'species', label: 'Species' },
    ],
  },
  {
    label: 'Brew Methods', entityName: 'Brew Method', hooks: brewMethodHooks,
    columns: [{ field: 'name', headerName: 'Name', flex: 1 }],
    fields: [{ name: 'name', label: 'Name', required: true }],
  },
  {
    label: 'Stop Modes', entityName: 'Stop Mode', hooks: stopModeHooks,
    columns: [{ field: 'name', headerName: 'Name', flex: 1 }],
    fields: [{ name: 'name', label: 'Name', required: true }],
  },
  {
    label: 'Vendors', entityName: 'Vendor', hooks: vendorHooks,
    columns: [
      { field: 'name', headerName: 'Name', flex: 1 },
      { field: 'url', headerName: 'URL', flex: 1 },
      { field: 'location', headerName: 'Location', flex: 1 },
    ],
    fields: [
      { name: 'name', label: 'Name', required: true },
      { name: 'url', label: 'URL' },
      { name: 'location', label: 'Location' },
      { name: 'notes', label: 'Notes' },
    ],
  },
  {
    label: 'Storage Types', entityName: 'Storage Type', hooks: storageTypeHooks,
    columns: [{ field: 'name', headerName: 'Name', flex: 1 }],
    fields: [{ name: 'name', label: 'Name', required: true }],
  },
];

export default function LookupsPage() {
  const [activeTab, setActiveTab] = useState(0);

  return (
    <>
      <PageHeader title="Lookups" />
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs
          value={activeTab}
          onChange={(_, v) => setActiveTab(v)}
          variant="scrollable"
          scrollButtons="auto"
        >
          {tabs.map((t) => (
            <Tab key={t.label} label={t.label} />
          ))}
        </Tabs>
      </Box>
      {tabs.map((t, i) =>
        activeTab === i ? (
          <LookupTab key={t.label} hooks={t.hooks} columns={t.columns} fields={t.fields} entityName={t.entityName} />
        ) : null,
      )}
    </>
  );
}
```

- [ ] **Step 4: Verify lookups page works**

Navigate to `/settings/lookups`. Verify tabs switch, CRUD works on each tab, search and retired toggle work.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/settings/
git commit -m "feat(frontend): implement Lookups page with 9 tabbed lookup types"
```

---

### Task 13: Beans Feature

**Files:**
- Create: `frontend/src/features/beans/hooks.ts`
- Modify: `frontend/src/features/beans/pages/BeansListPage.tsx`
- Modify: `frontend/src/features/beans/pages/BeanDetailPage.tsx`
- Create: `frontend/src/features/beans/components/BeanFormDialog.tsx`
- Create: `frontend/src/features/beans/components/BagFormDialog.tsx`

Follow the same pattern as People (Task 11) for hooks, but with:
- **Hooks:** `useBeans(params)`, `useBean(id)`, `useCreateBean()`, `useUpdateBean()`, `useDeleteBean()`, `useBags(beanId, params)`, `useCreateBag(beanId)`, `useUpdateBag(beanId)`, `useDeleteBag(beanId)`, `useBeanRatings(beanId, params)`, `useCreateBeanRating(beanId)`
- **BeansListPage:** DataGrid with columns: name, roaster (from nested `roaster.name`), bean_mix_type, bean_use_type, roast_degree. Filters for roaster_id, origin_id, process_id, variety_id using AutocompleteCreate in filter mode. Row click navigates to `/beans/:id`.
- **BeanFormDialog:** Complex form with all BeanCreate/BeanUpdate fields. M2M fields use AutocompleteCreate (origins with percentage, processes, varieties, flavor tags). Origins need a custom sub-form for `OriginWithPercentage` — each selected origin gets an optional percentage input.
- **BeanDetailPage:** Displays bean info card, inline bags DataGrid (via `GET /beans/{bean_id}/bags`), inline ratings DataGrid (via `GET /beans/{bean_id}/ratings`). "Add Bag", "Add Rating", "Edit Bean" buttons.
- **BagFormDialog:** Form with all BagCreate/BagUpdate fields. Vendor and storage type via AutocompleteCreate.

- [ ] **Step 1: Create beans/hooks.ts** with all hook functions as described above
- [ ] **Step 2: Create BeanFormDialog** with M2M fields (origins with percentage, processes, varieties, flavor tags)
- [ ] **Step 3: Create BagFormDialog** with date fields, vendor/storage type autocomplete
- [ ] **Step 4: Implement BeansListPage** with DataGrid, filters, row click navigation
- [ ] **Step 5: Implement BeanDetailPage** with bean info, bags grid, ratings grid, action buttons
- [ ] **Step 6: Verify beans CRUD works end-to-end**
- [ ] **Step 7: Commit**

```bash
git add frontend/src/features/beans/
git commit -m "feat(frontend): implement Beans feature with bags and ratings inline"
```

---

### Task 14: Bags List Page

**Files:**
- Modify: `frontend/src/features/bags/BagsListPage.tsx`
- Create: `frontend/src/features/bags/hooks.ts`

- [ ] **Step 1: Create bags/hooks.ts** — `useAllBags(params)` calling `GET /bags`, plus `useBeans` to resolve `bean_id` → `bean_name` (fetch all beans once, map by ID)
- [ ] **Step 2: Implement BagsListPage** — DataGrid with columns from `BagRead` (roast_date, weight, price, is_preground, opened_at, frozen_at), bean name resolved via client-side join. Filters: bean_id, is_preground, include_retired.
- [ ] **Step 3: Verify and commit**

```bash
git add frontend/src/features/bags/
git commit -m "feat(frontend): implement Bags list page with cross-bean view"
```

---

### Task 15: Equipment — Papers + Waters

**Files:**
- Create: `frontend/src/features/equipment/hooks.ts`
- Modify: `frontend/src/features/equipment/pages/PapersPage.tsx`
- Modify: `frontend/src/features/equipment/pages/WatersPage.tsx`
- Create: `frontend/src/features/equipment/components/PaperFormDialog.tsx`
- Create: `frontend/src/features/equipment/components/WaterFormDialog.tsx`

- [ ] **Step 1: Create equipment/hooks.ts** — hook functions for all 4 equipment types: `usePapers`, `useCreatePaper`, `useUpdatePaper`, `useDeletePaper`, same for waters, grinders, brewers
- [ ] **Step 2: Create PaperFormDialog** — simple: name + notes
- [ ] **Step 3: Implement PapersPage** — DataGrid (name, notes), add/edit/retire
- [ ] **Step 4: Create WaterFormDialog** — name, notes, dynamic minerals list (add/remove mineral_name + ppm rows)
- [ ] **Step 5: Implement WatersPage** — DataGrid (name, mineral count), add/edit/retire
- [ ] **Step 6: Verify and commit**

```bash
git add frontend/src/features/equipment/
git commit -m "feat(frontend): implement Papers and Waters equipment pages"
```

---

### Task 16: Equipment — Grinders

**Files:**
- Modify: `frontend/src/features/equipment/pages/GrindersPage.tsx`
- Create: `frontend/src/features/equipment/components/GrinderFormDialog.tsx`

- [ ] **Step 1: Create GrinderFormDialog** — name, dial_type (select: stepless/stepped), display_format, dynamic rings list (each ring: label, min, max, step fields). Add/remove ring rows dynamically.
- [ ] **Step 2: Implement GrindersPage** — DataGrid (name, dial_type, grind_range display), add/edit/retire
- [ ] **Step 3: Verify and commit**

```bash
git add frontend/src/features/equipment/
git commit -m "feat(frontend): implement Grinders equipment page"
```

---

### Task 17: Equipment — Brewers

**Files:**
- Modify: `frontend/src/features/equipment/pages/BrewersPage.tsx`
- Create: `frontend/src/features/equipment/components/BrewerFormDialog.tsx`

This is the most complex equipment form.

- [ ] **Step 1: Create BrewerFormDialog** — organized into collapsible sections:
  - **Basic:** name (required)
  - **Temperature:** temp_control_type (select: none/preset/pid/profiling), temp_min, temp_max, temp_step
  - **Pre-infusion:** preinfusion_type (select: none/fixed/timed/adjustable_pressure/programmable/manual), preinfusion_max_time
  - **Pressure:** pressure_control_type (select: fixed/opv_adjustable/electronic/manual_profiling/programmable), pressure_min, pressure_max
  - **Flow:** flow_control_type (select: none/manual_paddle/manual_valve/programmable), saturation_flow_rate
  - **Features:** has_bloom toggle
  - **M2M:** brew methods (AutocompleteCreate multi), stop modes (AutocompleteCreate multi)
- [ ] **Step 2: Implement BrewersPage** — DataGrid (name, brew methods chips, tier badge), add/edit/retire
- [ ] **Step 3: Verify and commit**

```bash
git add frontend/src/features/equipment/
git commit -m "feat(frontend): implement Brewers equipment page"
```

---

### Task 18: Brew Setups Feature

**Files:**
- Modify: `frontend/src/features/brew-setups/BrewSetupsPage.tsx`
- Create: `frontend/src/features/brew-setups/BrewSetupFormDialog.tsx`
- Create: `frontend/src/features/brew-setups/hooks.ts`

- [ ] **Step 1: Create brew-setups/hooks.ts** — `useBrewSetups(params)`, `useCreateBrewSetup()`, `useUpdateBrewSetup()`, `useDeleteBrewSetup()`
- [ ] **Step 2: Create BrewSetupFormDialog** — name, brew_method (AutocompleteCreate, required), grinder/brewer/paper/water (all AutocompleteCreate, optional)
- [ ] **Step 3: Implement BrewSetupsPage** — DataGrid (name, brew_method_name, grinder_name, brewer_name, paper_name, water_name), add/edit/retire
- [ ] **Step 4: Verify and commit**

```bash
git add frontend/src/features/brew-setups/
git commit -m "feat(frontend): implement Brew Setups feature"
```

---

### Task 19: Brews — Hooks + List Page

**Files:**
- Create: `frontend/src/features/brews/hooks.ts`
- Modify: `frontend/src/features/brews/pages/BrewsListPage.tsx`

- [ ] **Step 1: Create brews/hooks.ts** — `useBrews(params)`, `useBrew(id)`, `useCreateBrew()`, `useUpdateBrew()`, `useDeleteBrew()`, `useCreateBrewTaste(brewId)`, `useUpdateBrewTaste(brewId)`, `useDeleteBrewTaste(brewId)`. Brew mutations also invalidate `['stats', 'brews']` and `['stats', 'taste']`.
- [ ] **Step 2: Implement BrewsListPage** — DataGrid with `BrewListRead` columns (bean_name, brew_method_name, person_name, dose, grind_setting_display, temperature, score, brewed_at, is_failed as red chip). Filters: bag_id, bean_id, brew_setup_id, person_id, brewed_after, brewed_before (date pickers), include_retired. Row click navigates to `/brews/:id`.
- [ ] **Step 3: Verify list page loads and filters work**
- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/brews/hooks.ts frontend/src/features/brews/pages/BrewsListPage.tsx
git commit -m "feat(frontend): implement Brews list page with filters"
```

---

### Task 20: Brews — Wizard (3 Steps)

**Files:**
- Modify: `frontend/src/features/brews/components/BrewWizard.tsx`
- Create: `frontend/src/features/brews/components/BrewStepSetup.tsx`
- Create: `frontend/src/features/brews/components/BrewStepParams.tsx`
- Create: `frontend/src/features/brews/components/BrewStepTaste.tsx`

- [ ] **Step 1: Create BrewWizard** — MUI Stepper with 3 steps ("Setup", "Parameters", "Taste"). Manages shared wizard state in `useState`. Navigation: Back/Next buttons, Skip on step 3. On final submit: `POST /brews` with optional inline `taste` field. On success: navigate to `/brews/:newId`, invalidate queries.

- [ ] **Step 2: Create BrewStepSetup** — Bag picker (AutocompleteCreate), brew setup picker (AutocompleteCreate showing `name - brew_method_name`), person picker (AutocompleteCreate). All required.

- [ ] **Step 3: Create BrewStepParams** — grind_setting or grind_setting_display (text field — the API accepts either), temperature, pressure, flow_rate (number fields), dose (required), yield_amount, pre_infusion_time, total_time (number fields), stop_mode (AutocompleteCreate), is_failed (switch), notes (multiline), brewed_at (datetime picker, defaults to now).

- [ ] **Step 4: Create BrewStepTaste** — Optional step. Score slider (0-10), acidity/sweetness/body/bitterness/balance/aftertaste sliders (all 0-10), notes, FlavorTagSelect. Live TasteRadar preview using `brewTasteToRadar()` helper.

- [ ] **Step 5: Verify wizard flow end-to-end**

Start at `/brews/new`, fill all 3 steps, submit. Verify brew appears in list. Also verify skipping taste step works.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/brews/components/
git commit -m "feat(frontend): implement Brew wizard with 3-step flow"
```

---

### Task 21: Brews — Detail Page

**Files:**
- Modify: `frontend/src/features/brews/pages/BrewDetailPage.tsx`

- [ ] **Step 1: Implement BrewDetailPage** — Uses `useBrew(id)`. Displays:
  - Brew info card: bag (bean name), brew setup (equipment names), person, all parameters
  - Taste section: if taste exists, show TasteRadar + flavor tag chips + score. If no taste, show "Add Taste" button that opens a dialog (reuse BrewStepTaste form)
  - Edit/Delete actions in PageHeader
- [ ] **Step 2: Verify detail page loads and taste editing works**
- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/brews/pages/BrewDetailPage.tsx
git commit -m "feat(frontend): implement Brew detail page with taste"
```

---

### Task 22: Cuppings Feature

**Files:**
- Create: `frontend/src/features/cuppings/hooks.ts`
- Modify: `frontend/src/features/cuppings/pages/CuppingsListPage.tsx`
- Modify: `frontend/src/features/cuppings/pages/CuppingDetailPage.tsx`
- Create: `frontend/src/features/cuppings/components/CuppingFormDialog.tsx`

- [ ] **Step 1: Create cuppings/hooks.ts** — `useCuppings(params)`, `useCupping(id)`, `useCreateCupping()`, `useUpdateCupping()`, `useDeleteCupping()`. Mutations invalidate `['stats', 'cuppings']`.

- [ ] **Step 2: Create CuppingFormDialog** — bag (AutocompleteCreate), person (AutocompleteCreate), cupped_at datetime, 10 SCAA score sliders (0-9 range), cuppers_correction (number), total_score (auto-calculated or manual — show computed value, allow override), notes, FlavorTagSelect.

- [ ] **Step 3: Implement CuppingsListPage** — DataGrid with total_score, cupped_at, person_name. Client-side join for bag→bean name (fetch bags and beans, map by ID).

- [ ] **Step 4: Implement CuppingDetailPage** — Full score breakdown, TasteRadar with `cuppingToRadar()`, flavor tag chips, edit/delete actions.

- [ ] **Step 5: Verify and commit**

```bash
git add frontend/src/features/cuppings/
git commit -m "feat(frontend): implement Cuppings feature with SCAA scoring"
```

---

### Task 23: Ratings Feature

**Files:**
- Create: `frontend/src/features/ratings/hooks.ts`
- Modify: `frontend/src/features/ratings/RatingDetailPage.tsx`
- Create: `frontend/src/features/ratings/RatingFormDialog.tsx`

- [ ] **Step 1: Create ratings/hooks.ts** — `useRating(id)`, `useCreateBeanRating(beanId)`, `useDeleteRating()`, `useUpdateBeanTaste(ratingId)`, `useDeleteBeanTaste(ratingId)`. Note: ratings list is handled by beans hooks (`useBeanRatings`).

- [ ] **Step 2: Create RatingFormDialog** — person picker, inline taste form (score 0-10, acidity/sweetness/body/complexity/aroma/clean_cup sliders 0-10, notes, FlavorTagSelect). Opens from BeanDetailPage.

- [ ] **Step 3: Implement RatingDetailPage** — TasteRadar with `beanTasteToRadar()`, flavor tag chips, taste editable via PATCH. No edit on the rating itself (append-only).

- [ ] **Step 4: Verify and commit**

```bash
git add frontend/src/features/ratings/
git commit -m "feat(frontend): implement Ratings feature (inline on bean detail)"
```

---

### Task 24: Dashboard Feature

**Files:**
- Create: `frontend/src/features/dashboard/hooks.ts`
- Modify: `frontend/src/features/dashboard/DashboardPage.tsx`

- [ ] **Step 1: Create dashboard/hooks.ts** — 5 independent hooks:
  - `useBrewStats()` → `GET /stats/brews` → queryKey `['stats', 'brews']`
  - `useBeanStats()` → `GET /stats/beans` → queryKey `['stats', 'beans']`
  - `useTasteStats()` → `GET /stats/taste` → queryKey `['stats', 'taste']`
  - `useEquipmentStats()` → `GET /stats/equipment` → queryKey `['stats', 'equipment']`
  - `useCuppingStats()` → `GET /stats/cuppings` → queryKey `['stats', 'cuppings']`

- [ ] **Step 2: Implement DashboardPage** — Grid layout with StatsCard groups:
  - **Brew row:** Total brews, this week, fail rate, avg dose
  - **Bean row:** Total beans, active bags, bags unopened
  - **Taste row:** Best brew score (linked), mini TasteRadar of avg brew taste axes
  - **Equipment row:** Total grinders, total brewers, most used method
  - **Cupping row:** Total cuppings, avg total score, best total score
  - **Recent brews** list below: last 5 brews from `useBrews({ limit: 5, offset: 0, sort_by: 'brewed_at', sort_dir: 'desc' })`, rendered as simple MUI List items (not DataGrid — lighter weight for 5 items).

- [ ] **Step 3: Verify dashboard loads with real data from stats endpoints**
- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/dashboard/
git commit -m "feat(frontend): implement Dashboard with stats cards and recent brews"
```

---

### Task 25: Polish — Empty States + Error Handling + Build Verification

**Files:**
- Various feature pages (add empty state props to DataTable usage)

- [ ] **Step 1: Add meaningful empty states to all DataTable usages**

For each feature, set contextual `emptyTitle`, `emptyDescription`, and `emptyActionLabel` props. Examples:
- Beans: "No beans yet" / "Add your first coffee bean to get started" / "Add Bean"
- Brews: "No brews yet" / "Log your first brew to start tracking" / "Log a Brew"
- Equipment: "No grinders yet" / "Add your grinder to start building setups"

- [ ] **Step 2: Verify 422 validation error handling**

Submit an invalid form (e.g., blank name for a required field). Verify the Snackbar shows the validation error from the API.

- [ ] **Step 3: Verify 409 conflict handling**

Try to retire a lookup item that has dependencies. Verify the error is shown.

- [ ] **Step 4: Run production build**

```bash
cd /Users/fzills/tools/BeanBay/frontend && npm run build
```

Expected: Build succeeds with no TypeScript errors. Output in `dist/`.

- [ ] **Step 5: Commit any remaining fixes**

```bash
git add frontend/
git commit -m "feat(frontend): add empty states and verify build"
```

---

## Dependency Graph

```
Task 1 (scaffold)
  └── Task 2 (types)
  └── Task 3 (theme)
  └── Task 4 (API + notifications)
       └── Task 5 (entry + routing + pagination)
            └── Task 6 (AppLayout)
            └── Task 7 (PageHeader, ConfirmDialog, EmptyState)
            └── Task 8 (DataTable)
            └── Task 9 (AutocompleteCreate, FlavorTagSelect)
            └── Task 10 (StatsCard, TasteRadar)
                 ├── Task 11 (People) ←── pattern establisher
                 ├── Task 12 (Lookups)
                 ├── Task 13 (Beans)
                 │    └── Task 14 (Bags list)
                 │    └── Task 23 (Ratings)
                 ├── Task 15 (Papers + Waters)
                 ├── Task 16 (Grinders)
                 ├── Task 17 (Brewers)
                 ├── Task 18 (Brew Setups)
                 ├── Task 19 (Brews list)
                 │    └── Task 20 (Brew wizard)
                 │    └── Task 21 (Brew detail)
                 ├── Task 22 (Cuppings)
                 └── Task 24 (Dashboard)
                      └── Task 25 (Polish)
```

Tasks 11-24 (features) are independent of each other and can be parallelized after shared components (Tasks 1-10) are done. Task 13 (Beans) should be done before Task 14 (Bags) and Task 23 (Ratings) since those depend on bean hooks. Task 19 (Brews list) before Tasks 20-21. Task 25 (polish) is last.
