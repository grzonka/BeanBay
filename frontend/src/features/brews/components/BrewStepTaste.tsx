// frontend/src/features/brews/components/BrewStepTaste.tsx
import { Box, Grid, Slider, Stack, TextField, Typography } from '@mui/material';
import FlavorTagSelect from '@/components/FlavorTagSelect';
import TasteRadar, { brewTasteToRadar } from '@/components/TasteRadar';

interface FlavorTag { id: string; name: string; }

export interface TasteData {
  score: number | null;
  acidity: number | null;
  sweetness: number | null;
  body: number | null;
  bitterness: number | null;
  balance: number | null;
  aftertaste: number | null;
  notes: string;
  flavor_tags: FlavorTag[];
}

interface BrewStepTasteProps {
  data: TasteData;
  onChange: (patch: Partial<TasteData>) => void;
}

const AXES: { key: keyof Omit<TasteData, 'score' | 'notes' | 'flavor_tags'>; label: string }[] = [
  { key: 'acidity', label: 'Acidity' },
  { key: 'sweetness', label: 'Sweetness' },
  { key: 'body', label: 'Body' },
  { key: 'bitterness', label: 'Bitterness' },
  { key: 'balance', label: 'Balance' },
  { key: 'aftertaste', label: 'Aftertaste' },
];

function TasteSlider({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number | null;
  onChange: (v: number | null) => void;
}) {
  const displayValue = value ?? 0;

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Typography variant="body2">{label}</Typography>
        <Typography variant="body2" fontWeight="bold">
          {value != null ? value.toFixed(1) : '—'}
        </Typography>
      </Stack>
      <Slider
        value={displayValue}
        onChange={(_, v) => onChange(v as number)}
        min={0}
        max={10}
        step={0.5}
        valueLabelDisplay="auto"
        size="small"
      />
    </Box>
  );
}

export default function BrewStepTaste({ data, onChange }: BrewStepTasteProps) {
  const radarData = brewTasteToRadar({
    acidity: data.acidity,
    sweetness: data.sweetness,
    body: data.body,
    bitterness: data.bitterness,
    balance: data.balance,
    aftertaste: data.aftertaste,
  });

  return (
    <Stack spacing={3}>
      <Typography variant="body2" color="text.secondary">
        This step is optional. Skip if you don't want to record taste notes.
      </Typography>

      <Box>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography variant="body2">Overall Score</Typography>
          <Typography variant="body2" fontWeight="bold">
            {data.score != null ? data.score.toFixed(1) : '—'}
          </Typography>
        </Stack>
        <Slider
          value={data.score ?? 0}
          onChange={(_, v) => onChange({ score: v as number })}
          min={0}
          max={10}
          step={0.5}
          valueLabelDisplay="auto"
          marks={[
            { value: 0, label: '0' },
            { value: 5, label: '5' },
            { value: 10, label: '10' },
          ]}
        />
      </Box>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Stack spacing={1}>
            {AXES.map(({ key, label }) => (
              <TasteSlider
                key={key}
                label={label}
                value={data[key]}
                onChange={(v) => onChange({ [key]: v })}
              />
            ))}
          </Stack>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <TasteRadar data={radarData} size={260} />
        </Grid>
      </Grid>

      <FlavorTagSelect
        value={data.flavor_tags}
        onChange={(tags) => onChange({ flavor_tags: tags })}
      />

      <TextField
        label="Taste Notes"
        value={data.notes}
        onChange={(e) => onChange({ notes: e.target.value })}
        multiline
        rows={3}
        fullWidth
      />
    </Stack>
  );
}
