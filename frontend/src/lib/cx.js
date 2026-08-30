// Minimal className combiner — avoids an extra dependency.
export function cx(...args) {
  return args.filter(Boolean).join(' ');
}
