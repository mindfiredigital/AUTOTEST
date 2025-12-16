import React from 'react'
import { useParams } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { useSiteInfoQuery } from '@/utils/queries/sitesQuery'

const SiteInfoPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const { data, isLoading, isError } = useSiteInfoQuery(id!)

  if (isLoading) return <div className="flex justify-center py-20">Loading...</div>
  if (isError || !data) return <div className="text-center py-20">Error loading site info</div>

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="grid grid-cols-1 lg:grid-cols-[7fr_3fr] gap-6">
        <div className="flex flex-col gap-6">
          <Card>
            <CardHeader className="bg-red-50 border-b border-border">
              <CardTitle className="text-sm">Analyze Process</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <p className="mb-2">
                    {data.analyzeStatus === 'Processing' ? 'Processing...' : data.analyzeStatus}
                  </p>
                  {data.analyzeStatus === 'Processing' && (
                    <div className="flex space-x-1 mb-2">
                      {[...Array(7)].map((_, i) => (
                        <span
                          key={i}
                          className={`h-2 w-2 rounded-full ${i < 3 ? 'bg-red-500' : 'bg-gray-300'}`}
                        />
                      ))}
                    </div>
                  )}
                </div>
                <Button variant="outline" size="sm">
                  View Logs
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="bg-red-50 border-b border-border">
              <CardTitle className="text-sm">Site Dashboard</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {[
                  { label: 'Pages', value: data.stats.pages },
                  { label: 'Test Scenario', value: data.stats.testScenario },
                  { label: 'Test Cases', value: data.stats.testCases },
                  { label: 'Test Suite', value: data.stats.testSuite },
                  { label: 'Test Environment', value: data.stats.testEnvironment },
                  { label: 'Schedule Test Case', value: data.stats.scheduleTestCase },
                ].map((stat) => (
                  <Card key={stat.label} className="flex flex-col items-center justify-center p-4">
                    <CardContent className="text-center">
                      <p className="text-xs text-muted-foreground">{stat.label}</p>
                      <p className="text-lg font-semibold">{stat.value}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="h-full">
          <CardHeader className="bg-red-50 border-b border-border">
            <CardTitle className="text-sm">Site Detail</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div>
              <p className="text-xs text-muted-foreground">Created On</p>
              <p>{new Date(data.createdAt).toLocaleString()}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Updated On</p>
              <p>{new Date(data.updatedAt).toLocaleString()}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Site Title</p>
              <p>{data.title}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Site URL</p>
              <a
                href={data.url}
                target="_blank"
                rel="noreferrer"
                className="text-primary hover:underline"
              >
                {data.url}
              </a>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default SiteInfoPage
