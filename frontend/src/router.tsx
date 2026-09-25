import { createRootRoute, createRoute, createRouter, Outlet } from "@tanstack/react-router";
import { IndexRoute } from "./routes/index";
import { ScanRoute } from "./routes/scans.$id";
const rootRoute = createRootRoute({ component: () => <><Outlet /></> });
const indexRoute = createRoute({ getParentRoute: () => rootRoute, path: "/", component: IndexRoute });
const scanRoute = createRoute({ getParentRoute: () => rootRoute, path: "/scans/$id", component: ScanRoute });
export const routeTree = rootRoute.addChildren([indexRoute, scanRoute]);
export const router = createRouter({ routeTree });
declare module "@tanstack/react-router" { interface Register { router: typeof router; } }
