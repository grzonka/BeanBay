import { useState } from 'react';
import { type GridColDef } from '@mui/x-data-grid';
import { Button } from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import PageHeader from '@/components/PageHeader';
import DataTable from '@/components/DataTable';
import { usePaginationParams } from '@/utils/pagination';
import { useBeans, type Bean } from '../hooks';
import BeanFormDialog from '../components/BeanFormDialog';

const columns: GridColDef<Bean>[] = [
  { field: 'name', headerName: 'Name', flex: 1, minWidth: 150 },
  {
    field: 'roaster',
    headerName: 'Roaster',
    width: 160,
    renderCell: (params) => params.row.roaster?.name ?? '—',
    sortable: false,
  },
  { field: 'bean_mix_type', headerName: 'Mix Type', width: 130 },
  { field: 'bean_use_type', headerName: 'Use Type', width: 120 },
  { field: 'roast_degree', headerName: 'Roast Degree', width: 130 },
  {
    field: 'bags',
    headerName: 'Bags',
    width: 80,
    renderCell: (params) => params.row.bags?.length ?? 0,
    sortable: false,
  },
];

export default function BeansListPage() {
  const {
    params, paginationModel, sortModel,
    onPaginationModelChange, onSortModelChange,
    setSearch, setIncludeRetired,
  } = usePaginationParams('name');

  const { data, isLoading } = useBeans(params);
  const [formOpen, setFormOpen] = useState(false);
  const [editBean, setEditBean] = useState<Bean | null>(null);

  return (
    <>
      <PageHeader
        title="Beans"
        actions={
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => { setEditBean(null); setFormOpen(true); }}
          >
            Add Bean
          </Button>
        }
      />
      <DataTable<Bean>
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
        detailPath={(row) => `/beans/${row.id}`}
        emptyTitle="No beans yet"
        emptyActionLabel="Add Bean"
        onEmptyAction={() => { setEditBean(null); setFormOpen(true); }}
      />
      <BeanFormDialog
        open={formOpen}
        onClose={() => setFormOpen(false)}
        bean={editBean}
      />
    </>
  );
}
