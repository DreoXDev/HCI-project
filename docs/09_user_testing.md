# User Testing

## Task Definition

Tasks should be realistic, comparable across systems and measurable. Define ids such as `T01`, `T02`, `T03` in `config/tasks.yaml`.

## Effectiveness

Effectiveness tracks completion. Absolute effectiveness is stricter and counts only autonomous success without critical issues.

## Efficiency

Efficiency uses task completion time, usually only for autonomous successes. OET thresholds are configured in analysis settings.

## Errors And Help

Record errors, help requests and observer notes. Partial completions should not be silently treated as clean successes.

## Statistical Tests

The project uses paired comparisons because the same users evaluate both systems. The pipeline selects tests according to the metric and available paired data.
