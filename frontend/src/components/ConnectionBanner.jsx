import { Dot } from './ui';

export default function ConnectionBanner({ connectionState, status, errorMessage, onReconnect }) {
  const done = status === 'COMPLETED';
  const isError = status === 'ERROR' || connectionState === 'error';

  if (isError) {
    return (
      <div
        role="alert"
        className="border-b border-flagged/25 bg-flagged-soft px-4 py-2.5 text-center text-[13px] text-flagged sm:px-6"
      >
        {errorMessage || 'The debate stream encountered an error.'}
        {onReconnect && (
          <button
            type="button"
            onClick={onReconnect}
            className="ml-2 font-semibold underline underline-offset-2 hover:no-underline"
          >
            Reconnect
          </button>
        )}
      </div>
    );
  }

  if (connectionState === 'closed' && !done) {
    return (
      <div
        role="status"
        className="flex items-center justify-center gap-2 border-b border-caution/25 bg-caution-soft px-4 py-2.5 text-center text-[13px] text-caution sm:px-6"
      >
        <Dot tone="caution" />
        Live connection closed.
        <button
          type="button"
          onClick={onReconnect}
          className="font-semibold underline underline-offset-2 hover:no-underline"
        >
          Reconnect
        </button>
      </div>
    );
  }

  return null;
}
