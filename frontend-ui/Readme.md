# Smart Browsing Agent Frontend

Frontend-only AI browser/search UI built with Next.js 15, TypeScript, TailwindCSS, Zustand, and Lucide React.

## Run

```bash
npm install
npm run dev
```

The app expects the backend at `http://localhost:8000` with:

- `POST /query`
- body: `{ "query": "..." }`
- response: `{ "response": "..." }`

## Environment

Optional override:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```
