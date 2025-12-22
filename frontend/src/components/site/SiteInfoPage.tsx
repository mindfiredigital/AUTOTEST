import React from 'react'
import { useParams } from 'react-router-dom'
import { FileText, List, Database, GitBranch, Layout, Calendar } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface SiteStats {
  pages: number
  testScenario: number
  testCases: number
  testSuite: number
  testEnvironment: number
  scheduleTestCase: number
}

interface SiteInfoData {
  id: string
  title: string
  url: string
  createdAt: string
  updatedAt: string
  stats: SiteStats
}

// Temporary mock data until API / query hooks are wired
const getMockSiteInfo = (id: string): SiteInfoData => ({
  id,
  title: 'Admin Dashboard Portal',
  url: 'https://dashboard.example.com',
  createdAt: '2025-08-25T10:30:00Z',
  updatedAt: '2025-08-26T15:45:00Z',
  stats: {
    pages: 24,
    testScenario: 8,
    testCases: 120,
    testSuite: 5,
    testEnvironment: 3,
    scheduleTestCase: 18,
  },
})

const SiteInfoPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()

  // In a real app this would come from an API:
  const data = getMockSiteInfo(id || '1')

  const dashboardStats = [
    { label: 'Pages', value: data.stats.pages, icon: <FileText className="w-5 h-5" /> },
    { label: 'Test Scenario', value: data.stats.testScenario, icon: <List className="w-5 h-5" /> },
    { label: 'Test Cases', value: data.stats.testCases, icon: <Database className="w-5 h-5" /> },
    { label: 'Test Suite', value: data.stats.testSuite, icon: <GitBranch className="w-5 h-5" /> },
    {
      label: 'Test Environment',
      value: data.stats.testEnvironment,
      icon: <Layout className="w-5 h-5" />,
    },
    {
      label: 'Schedule Test Case',
      value: data.stats.scheduleTestCase,
      icon: <Calendar className="w-5 h-5" />,
    },
  ]

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[6.5fr_3.5fr] gap-8 mx-auto">
      {/* LEFT COLUMN */}
      <div className="flex flex-col gap-8">
        {/* Analyze Process Card */}
        <div className="border border-[#E4D7D7] bg-white rounded-[6px] overflow-hidden shadow-none">
          <div className="bg-[#FFF8F8] border-b border-[#E4D7D7] py-3 px-4">
            <h2 className="text-[15px] font-semibold text-[#322525]">Analyze Process</h2>
          </div>
          <div className="p-5">
            <div className="flex items-center justify-between gap-4">
              <div className="flex flex-col gap-3">
                <p className="text-sm text-[#7A6060] font-medium">Processing...</p>
                <div className="flex space-x-1.5">
                  {[...Array(12)].map((_, i) => (
                    <span
                      key={i}
                      className={`h-2.5 w-2.5 rounded-full ${
                        i < 3 ? 'bg-[#E63B3B]' : 'bg-[#E5D6D6]'
                      }`}
                    />
                  ))}
                </div>
              </div>
              <Button
                variant="outline"
                className="border-[#E63B3B] text-[#E63B3B] hover:bg-[#FFF0F0] hover:text-[#BF2F2F] px-6 font-medium rounded-md"
              >
                View Logs
              </Button>
            </div>
          </div>
        </div>

        {/* Site Dashboard Card */}
        <div className="border border-[#E4D7D7] bg-white rounded-[6px] overflow-hidden shadow-none">
          <div className="bg-[#FFF8F8] border-b border-[#E4D7D7] py-3 px-4">
            <h2 className="text-[15px] font-semibold text-[#322525]">Site Dashboard</h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {dashboardStats.map((stat) => (
                <div
                  key={stat.label}
                  className="flex items-center border border-[#EFE3E3] rounded-lg p-4 bg-white hover:shadow-sm transition-shadow"
                >
                  <div className="bg-[#F6F0F0] p-3 rounded-lg mr-4 text-[#6B5555] border border-[#EFE3E3]">
                    {stat.icon}
                  </div>
                  <div className="flex flex-col">
                    <span className="text-xs font-medium text-[#8B6E6E] mb-0.5">{stat.label}</span>
                    <span className="text-2xl font-bold text-[#2B1F1F]">{stat.value}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* RIGHT COLUMN - Site Detail */}
      <div className="border border-[#E4D7D7] bg-white rounded-[6px] overflow-hidden h-fit">
        <div className="bg-[#FFF8F8] border-b border-[#E4D7D7] py-3 px-4">
          <h2 className="text-[15px] font-semibold text-[#322525]">Site Detail</h2>
        </div>
        <div className="p-6 space-y-6">
          <DetailItem
            label="Created On"
            value={new Date(data.createdAt).toLocaleString('en-GB', {
              day: '2-digit',
              month: '2-digit',
              year: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            })}
          />
          <DetailItem
            label="Updated On"
            value={new Date(data.updatedAt).toLocaleString('en-GB', {
              day: '2-digit',
              month: '2-digit',
              year: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            })}
          />
          <DetailItem label="Site Title" value={data.title} />
          <div>
            <p className="text-[11px] font-semibold text-[#8B6E6E] uppercase tracking-[0.08em] mb-1.5">
              Site URL
            </p>
            <a
              href={data.url}
              target="_blank"
              rel="noreferrer"
              className="text-[#2761FF] hover:underline text-sm break-all font-medium"
            >
              {data.url}
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}

const DetailItem: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div>
    <p className="text-[11px] font-semibold text-[#8B6E6E] uppercase tracking-[0.08em] mb-1.5">
      {label}
    </p>
    <p className="text-sm text-[#2B1F1F] font-medium leading-relaxed">{value}</p>
  </div>
)

export default SiteInfoPage
