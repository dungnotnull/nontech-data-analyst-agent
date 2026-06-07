import { Database, Hash, Calendar, Type, DollarSign } from 'lucide-react'
import type { SchemaInfo } from '../types'

const typeIcons: Record<string, React.ReactNode> = {
  numeric: <Hash className="w-3.5 h-3.5" />,
  currency: <DollarSign className="w-3.5 h-3.5" />,
  datetime: <Calendar className="w-3.5 h-3.5" />,
  categorical: <Database className="w-3.5 h-3.5" />,
  text: <Type className="w-3.5 h-3.5" />,
  percentage: <Hash className="w-3.5 h-3.5" />,
}

const typeColors: Record<string, string> = {
  numeric: 'bg-blue-100 text-blue-700',
  currency: 'bg-green-100 text-green-700',
  datetime: 'bg-purple-100 text-purple-700',
  categorical: 'bg-amber-100 text-amber-700',
  text: 'bg-gray-100 text-gray-700',
  percentage: 'bg-cyan-100 text-cyan-700',
  empty: 'bg-red-100 text-red-700',
}

const roleLabelsVi: Record<string, string> = {
  date: 'Ngày',
  metric_revenue: 'Doanh thu',
  metric_cost: 'Chi phí',
  metric_quantity: 'Số lượng',
  metric_profit: 'Lợi nhuận',
  metric: 'Chỉ số',
  dimension_product: 'Sản phẩm',
  dimension_region: 'Khu vực',
  dimension_customer: 'Khách hàng',
  dimension: 'Danh mục',
  other: 'Khác',
}

interface Props {
  schemas: Record<string, SchemaInfo>
}

export function SchemaViewer({ schemas }: Props) {
  const sheetNames = Object.keys(schemas)

  if (sheetNames.length === 0) return null

  return (
    <div className="space-y-3">
      {sheetNames.map((sheet) => {
        const schema = schemas[sheet]
        const roles = schema.suggested_roles || {}

        return (
          <div key={sheet} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <div className="flex items-center gap-2 mb-3">
              <Database className="w-4 h-4 text-brand-600" />
              <span className="font-semibold text-gray-800 text-sm">
                {sheetNames.length > 1 ? `Sheet: ${sheet}` : 'Cấu trúc dữ liệu'}
              </span>
              <span className="text-xs text-gray-500">
                {schema.columns.length} cột · {schema.row_count.toLocaleString()} dòng
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
              {schema.columns.map((col) => {
                const colType = schema.column_types?.[col] || 'text'
                const role = roles[col] || ''
                const missing = schema.missing_values?.[col] || 0
                const missingPct = schema.row_count > 0 ? ((missing / schema.row_count) * 100) : 0

                return (
                  <div key={col} className="flex items-center justify-between bg-white rounded-md px-3 py-2 border border-gray-100">
                    <div className="min-w-0 flex-1 mr-2">
                      <p className="text-sm font-medium text-gray-800 truncate" title={col}>
                        {col}
                      </p>
                      <div className="flex items-center gap-1.5 mt-0.5">
                        <span className={`inline-flex items-center gap-1 text-xs px-1.5 py-0.5 rounded-full ${typeColors[colType] || 'bg-gray-100 text-gray-600'}`}>
                          {typeIcons[colType] || <Type className="w-3 h-3" />}
                          {colType}
                        </span>
                        {role && (
                          <span className="text-xs text-brand-600 bg-brand-50 px-1.5 py-0.5 rounded-full">
                            {roleLabelsVi[role] || role}
                          </span>
                        )}
                      </div>
                    </div>
                    {missingPct > 20 && (
                      <span className="text-xs text-red-500 font-medium whitespace-nowrap" title={`${missing} giá trị thiếu`}>
                        {missingPct.toFixed(0)}% thiếu
                      </span>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )
      })}
    </div>
  )
}
