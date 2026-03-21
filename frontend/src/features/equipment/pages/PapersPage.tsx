import { useState } from 'react';
import { type GridColDef } from '@mui/x-data-grid';
import { Button } from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import PageHeader from '@/components/PageHeader';
import DataTable from '@/components/DataTable';
import ConfirmDialog from '@/components/ConfirmDialog';
import { usePaginationParams } from '@/utils/pagination';
import { paperHooks, type Paper } from '../hooks';
import PaperFormDialog from '../components/PaperFormDialog';
import { useNotification } from '@/components/NotificationProvider';

const columns: GridColDef[] = [
  { field: 'name', headerName: 'Name', flex: 1, minWidth: 150 },
  { field: 'notes', headerName: 'Notes', flex: 1, minWidth: 150 },
];

export default function PapersPage() {
  const { params, paginationModel, sortModel, onPaginationModelChange, onSortModelChange, setSearch, setIncludeRetired } =
    usePaginationParams('name');
  const { data, isLoading } = paperHooks.useList(params);
  const deletePaper = paperHooks.useDelete();
  const { notify } = useNotification();

  const [formOpen, setFormOpen] = useState(false);
  const [editPaper, setEditPaper] = useState<Paper | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Paper | null>(null);

  const handleDelete = async () => {
    if (deleteTarget) {
      await deletePaper.mutateAsync(deleteTarget.id);
      notify('Paper retired');
      setDeleteTarget(null);
    }
  };

  return (
    <>
      <PageHeader
        title="Papers"
        actions={
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => { setEditPaper(null); setFormOpen(true); }}
          >
            Add Paper
          </Button>
        }
      />
      <DataTable<Paper>
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
        emptyTitle="No papers yet"
        emptyActionLabel="Add Paper"
        onEmptyAction={() => { setEditPaper(null); setFormOpen(true); }}
      />
      <PaperFormDialog open={formOpen} onClose={() => setFormOpen(false)} paper={editPaper} />
      <ConfirmDialog
        open={!!deleteTarget}
        title="Retire Paper"
        message={`Retire "${deleteTarget?.name}"?`}
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </>
  );
}
