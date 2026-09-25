import { UrlInputBar } from "../components/UrlInputBar";

export function IndexRoute() {
  return (
    <div className="flex min-h-screen flex-col bg-paper text-ink">
      <header className="flex min-h-16 items-center justify-between border-b border-rule bg-paper px-[max(22px,calc((100vw-1120px)/2))] max-sm:px-[17px]">
        <div className="flex items-center gap-[11px] whitespace-nowrap text-sm font-bold tracking-tight max-[380px]:gap-2 max-[380px]:text-xs">
          <span className="grid h-7 w-7 place-items-center bg-ink text-[9px] tracking-[.05em] text-paper max-[380px]:h-[25px] max-[380px]:w-[25px] max-[380px]:text-[8px]">
            WA
          </span>
          <span>Website Archaeologist</span>
        </div>
        <span className="flex items-center gap-2 text-xs text-[#667064] max-sm:hidden">
          <i className="h-1.5 w-1.5 rounded-full bg-signal" /> Analysis service
          online
        </span>
      </header>
      <main className="mx-auto w-[min(100%-44px,1120px)] flex-1 py-[88px] pb-[70px] max-sm:w-[min(100%-32px,1120px)] max-sm:py-[58px] max-sm:pb-[45px]">
        <div className="mb-[34px] max-w-[600px]">
          <p className="mb-3 text-xs font-semibold text-signal">
            Website intelligence
          </p>
          <h1 className="m-0 max-w-[590px] text-[clamp(34px,4vw,52px)] font-bold leading-[1.05] tracking-[-.04em] max-sm:text-4xl max-[380px]:text-[31px]">
            Understand what a website is built from.
          </h1>
          <p className="mb-0 mt-[19px] max-w-[510px] text-base leading-relaxed text-[#5c665e]">
            Inspect the technologies, API routes, SEO signals, and performance
            characteristics behind any public website.
          </p>
        </div>
        <UrlInputBar />
        <div className="mt-[54px] grid grid-cols-3 border-y border-rule max-sm:mt-10 max-sm:grid-cols-1">
          {[
            ["Tech stack", "Frameworks, hosting, and libraries"],
            ["API routes", "Endpoints found in HTML and bundles"],
            ["SEO & performance", "Metadata, timing, and page weight"],
          ].map(([title, text], index) => (
            <div
              key={title}
              className={`flex flex-col gap-[5px] py-[15px] ${index > 0 ? "border-l border-rule pl-[22px] max-sm:border-l-0 max-sm:border-t max-sm:pl-0" : ""}`}
            >
              <strong className="text-[13px]">{title}</strong>
              <span className="text-xs text-[#6f786f]">{text}</span>
            </div>
          ))}
        </div>
      </main>
      <footer className="p-5 text-center text-[11px] text-[#7b837b]">
        Evidence-based website analysis · No account required
      </footer>
    </div>
  );
}
