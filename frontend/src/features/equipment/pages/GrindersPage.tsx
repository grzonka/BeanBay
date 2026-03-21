import { useState } from 'react';
import { type GridColDef } from '@mui/x-data-grid';
import { Button } from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import PageHeader from '@/components/PageHeader';
import DataTable from '@/components/DataTable';
import ConfirmDialog from '@/components/ConfirmDialog';
import { usePaginationParams } from '@/utils/pagination';
import { grinderHooks, type Grinder } from '../hooks';
import GrinderFormDialog from '../components/GrinderFormDialog';
import { useNotification } from '@/components/NotificationProvider';

const columns: GridColDef[] = [
  { field: 'name', headerName: 'Name', flex: 1, minWidth: 150 },
  { field: 'dial_type', headerName: 'Dial Type', width: 120 },
  {
    field: 'grind_range',
    headerName: 'Grind Range',
    width: 150,
    renderCell: (params) => {
      const range = params.value as Grinder['grind_range'];
      if (!range) return '—';
      return `${range.min} - ${range.max}`;
    },
  },
];

export default function GrindersPage() {
  const { params, paginationModel, sortModel, onPaginationModelChange, onSortModelChange, setSearch, setIncludeRetired } =
    usePaginationParams('name');
  const { data, isLoading } = grinderHooks.useList(params);
  const deleteGrinder = grinderHooks.useDelete();
  const { notify } = useNotification();

  const [formOpen, setFormOpen] = useState(false);
  const [editGrinder, setEditGrinder] = useState<Grinder | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Grinder | null>(null);

  const handleDelete = async () => {
    if (deleteTarget) {
      await deleteGrinder.mutateAsync(deleteTarget.id);
      notify('Grinder retired');
      setDeleteTarget(null);
    }
  };

  return (
    <>
      <PageHeader
        title="Grinders"
        actions={
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => { setEditGrinder(null); setFormOpen(true); }}
          >
            Add Grinder
          </Button>
        }
      />
      <DataTable<Grinder>
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
        emptyTitle="No grinders yet"
        emptyActionLabel="Add Grinder"
        onEmptyAction={() => { setEditGrinder(null); setFormOpen(true); }}
      />
      <GrinderFormDialog
        open={formOpen}
        onClose={() => setFormOpen(false)}
        grinder={editGrinder}
      />
      <ConfirmDialog
        open={!!deleteTarget}
        title="Retire Grinder"
        message={`Retire "${deleteTarget?.name}"? This won't delete associated brews.`}
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </>
  );
}
