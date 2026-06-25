# Data Requirements

## Project Data

- app A name;
- app B name;
- brand colors;
- logo/icon paths;
- app descriptions;
- rating/download/store data and collection date;
- comparison objective;
- context of use.

## Expert Evaluators

Minimum fields:

- evaluator id;
- group/type, if used;
- gender;
- age or age group;
- occupation;
- domain familiarity;
- usability experience;
- domain experience;
- notes.

## Heuristic Evaluation

Minimum fields:

- app/system;
- evaluator id;
- problem id;
- problem description;
- violated heuristic;
- severity;
- frequency or impact, if used;
- redesign suggestion;
- screenshot or screen reference, if available.

## User Testing

Minimum fields:

- anonymous user id;
- group, if used;
- app;
- task id;
- completion status;
- success/failure;
- time;
- errors;
- help/interventions;
- observer notes.

## UEQ/NPS Questionnaire

Minimum fields:

- anonymous user id;
- app;
- `Q01` to `Q26` UEQ items;
- NPS;
- optional additional questions;
- optional qualitative answers.

## Privacy

Do not commit names, emails, phone numbers, addresses, exact locations, recordings, screenshots with personal data, or unnecessary raw identifiers. Anonymize before importing.

Templates are available in `templates/data/`; schemas are documented in `schemas/`.
