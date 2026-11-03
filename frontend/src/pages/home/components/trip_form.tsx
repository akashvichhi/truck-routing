import { AddressInput } from '@src/pages/home/components/address_input'
import { LabeledInput } from '@src/ui/form/labeled_input'

interface ITripFormValues {
  origin: string
  destination: string
  departureDatetime: string
  loadWeightLbs: string
}

interface ITripFormErrors {
  origin?: string
  destination?: string
  departureDatetime?: string
  loadWeightLbs?: string
}

interface ITripFormProps {
  values: ITripFormValues
  errors: ITripFormErrors
  isLoading: boolean
  onFieldChange: (field: keyof ITripFormValues, value: string) => void
  onSubmit: () => void
}

export function TripForm({
  values,
  errors,
  isLoading,
  onFieldChange,
  onSubmit,
}: ITripFormProps): React.JSX.Element {
  function handleSubmit(e: React.FormEvent): void {
    e.preventDefault()
    onSubmit()
  }

  return (
    <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
      <AddressInput
        error={errors.origin}
        id="origin"
        label="Origin"
        placeholder="e.g. Chicago, IL"
        value={values.origin}
        onChange={(v: string): void => onFieldChange('origin', v)}
      />
      <AddressInput
        error={errors.destination}
        id="destination"
        label="Destination"
        placeholder="e.g. Dallas, TX"
        value={values.destination}
        onChange={(v: string): void => onFieldChange('destination', v)}
      />
      <LabeledInput
        error={errors.departureDatetime}
        id="departureDatetime"
        label="Departure Date & Time"
        type="datetime-local"
        value={values.departureDatetime}
        onChange={(v: string): void => onFieldChange('departureDatetime', v)}
      />
      <LabeledInput
        error={errors.loadWeightLbs}
        id="loadWeightLbs"
        label="Load Weight (lbs)"
        min="0"
        placeholder="e.g. 45000"
        step="500"
        type="number"
        value={values.loadWeightLbs}
        onChange={(v: string): void => onFieldChange('loadWeightLbs', v)}
      />
      <button
        className="mt-2 rounded-md bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow hover:bg-blue-700 disabled:opacity-60"
        disabled={isLoading}
        type="submit"
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            Calculating routes…
          </span>
        ) : (
          'Find Safe Routes'
        )}
      </button>
    </form>
  )
}
