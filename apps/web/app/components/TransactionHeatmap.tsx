'use client'

interface HeatmapCell {
  hour: number
  day: string
  count: number
}

interface TransactionHeatmapProps {
  data: HeatmapCell[]
}

const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const hours = Array.from({ length: 24 }, (_, i) => i)

export function TransactionHeatmap({ data }: TransactionHeatmapProps) {
  const getColor = (count: number, max: number) => {
    if (count === 0) return 'bg-gray-100'
    const intensity = Math.min((count / max) * 100, 100)
    if (intensity < 25) return 'bg-red-200'
    if (intensity < 50) return 'bg-red-300'
    if (intensity < 75) return 'bg-red-400'
    return 'bg-red-600'
  }

  const maxCount = Math.max(...data.map(d => d.count), 1)

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">🔥 Fraud Activity Heatmap</h2>
      <p className="text-sm text-gray-600 mb-4">Fraud incidents by day and hour</p>
      <div className="overflow-x-auto">
        <div className="inline-block min-w-full">
          <div className="flex">
            <div className="w-12"></div>
            <div className="flex-1 grid grid-cols-24 gap-1">
              {hours.map(hour => (
                <div key={hour} className="text-xs text-center text-gray-500">
                  {hour}
                </div>
              ))}
            </div>
          </div>
          {days.map(day => (
            <div key={day} className="flex items-center mt-1">
              <div className="w-12 text-xs text-gray-600 font-medium">{day}</div>
              <div className="flex-1 grid grid-cols-24 gap-1">
                {hours.map(hour => {
                  const cell = data.find(d => d.day === day && d.hour === hour)
                  const count = cell?.count || 0
                  return (
                    <div
                      key={`${day}-${hour}`}
                      className={`h-8 rounded ${getColor(count, maxCount)} hover:ring-2 ring-blue-500 transition-all cursor-pointer`}
                      title={`${day} ${hour}:00 - ${count} incidents`}
                    />
                  )
                })}
              </div>
            </div>
          ))}
          <div className="mt-4 flex items-center justify-end gap-2 text-xs text-gray-600">
            <span>Less</span>
            <div className="flex gap-1">
              <div className="w-4 h-4 bg-gray-100 rounded"></div>
              <div className="w-4 h-4 bg-red-200 rounded"></div>
              <div className="w-4 h-4 bg-red-300 rounded"></div>
              <div className="w-4 h-4 bg-red-400 rounded"></div>
              <div className="w-4 h-4 bg-red-600 rounded"></div>
            </div>
            <span>More</span>
          </div>
        </div>
      </div>
    </div>
  )
}

