# Website Archaeologist frontend

React + TypeScript + Vite frontend using TanStack Query and TanStack Router.

## Run

Start the backend on port 8000, then:

```bash
npm install
npm run dev
```

Open `http://localhost:5173`.

The frontend defaults to the deployed Railway API at:

```text
https://weblogist-production.up.railway.app
```

To use a different API, set `VITE_API_BASE_URL` before building:

```bash
VITE_API_BASE_URL=https://your-api.example.com npm run build
```

## Deploy to Vercel

Import the repository into Vercel and set the project root directory to `frontend`. The included `vercel.json` uses:

- Build command: `npm run build`
- Output directory: `dist`

Set this Vercel environment variable if you want to override the default API URL:

```text
VITE_API_BASE_URL=https://weblogist-production.up.railway.app
```

Vite embeds `VITE_API_BASE_URL` during the build, so redeploy after changing it. The production build is written to `dist/`.
