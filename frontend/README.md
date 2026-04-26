# AnyAlert Frontend (Next.js)

Feature-oriented architecture with App Router:

- `src/app` - route layer and layout
- `src/features` - isolated business features (auth, alerts, profile)
- `src/lib` - shared technical modules (api client, env, utils)
- `src/shared` - shared types and constants
- `src/components` - reusable UI components

## Run

```bash
npm install
copy .env.example .env.local
npm run dev
```
