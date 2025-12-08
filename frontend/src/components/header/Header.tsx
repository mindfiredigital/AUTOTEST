import NavLinks from './Helper'

export default function Header() {
  return (
    <header
      role="banner"
      className="sticky top-0 z-50 shadow-sm border-b bg-white dark:bg-gray-900"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-6">
            <h1 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white">
              <a href="/" aria-label="Go to Dam Platform Home">
                Autotest
              </a>
            </h1>
          </div>

          <NavLinks />
        </div>
      </div>
    </header>
  )
}
