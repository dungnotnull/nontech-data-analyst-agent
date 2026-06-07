import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileSpreadsheet, XCircle, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { uploadFile } from '../services/api'
import { useAppStore } from '../hooks/useStore'
import { SchemaViewer } from './SchemaViewer'

export function FileUpload() {
  const { sessionId, fileName, fileSizeMb, schemas, setSession, setError, clearSession, isLoading, setLoading } =
    useAppStore()
  const [previewSchema, setPreviewSchema] = useState(false)

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0]
      if (!file) return

      const ext = file.name.split('.').pop()?.toLowerCase()
      if (!ext || !['xlsx', 'xls', 'csv', 'tsv'].includes(ext)) {
        toast.error('Vui lòng chọn file Excel (.xlsx, .xls) hoặc CSV/TSV')
        return
      }

      if (file.size > 50 * 1024 * 1024) {
        toast.error('File quá lớn. Vui lòng chọn file dưới 50MB')
        return
      }

      setLoading(true)
      setError(null)

      try {
        const data = await uploadFile(file)
        setSession(data)
        toast.success(`Đã tải lên: ${data.file_name}`)
        setPreviewSchema(true)
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Lỗi tải file'
        setError(message)
        toast.error(message)
      } finally {
        setLoading(false)
      }
    },
    [setSession, setError, setLoading],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'text/csv': ['.csv', '.tsv'],
    },
    maxFiles: 1,
    disabled: isLoading,
  })

  if (sessionId && fileName) {
    return (
      <div className="animate-fade-in">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-brand-100 rounded-lg flex items-center justify-center">
              <FileSpreadsheet className="w-5 h-5 text-brand-600" />
            </div>
            <div>
              <p className="font-semibold text-gray-900">{fileName}</p>
              <p className="text-sm text-gray-500">{fileSizeMb?.toFixed(1)} MB</p>
            </div>
          </div>
          <button
            onClick={() => {
              clearSession()
              setPreviewSchema(false)
            }}
            className="p-2 text-gray-400 hover:text-red-500 rounded-lg hover:bg-red-50 transition-colors"
          >
            <XCircle className="w-5 h-5" />
          </button>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setPreviewSchema(!previewSchema)}
            className="text-sm text-brand-600 hover:text-brand-700 font-medium"
          >
            {previewSchema ? 'Ẩn cấu trúc dữ liệu' : 'Xem cấu trúc dữ liệu'}
          </button>
        </div>

        {previewSchema && schemas && (
          <div className="mt-3 animate-slide-up">
            <SchemaViewer schemas={schemas} />
          </div>
        )}
      </div>
    )
  }

  return (
    <div
      {...getRootProps()}
      className={`relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200
        ${isDragActive ? 'border-brand-500 bg-brand-50' : 'border-gray-300 hover:border-brand-400 hover:bg-gray-50'}
        ${isLoading ? 'opacity-50 pointer-events-none' : ''}`}
    >
      <input {...getInputProps()} />
      {isLoading ? (
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-10 h-10 text-brand-500 animate-spin" />
          <p className="text-gray-600 font-medium">Đang tải file lên...</p>
        </div>
      ) : (
        <>
          <Upload className="w-10 h-10 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-700 font-medium mb-1">
            Kéo thả file vào đây hoặc <span className="text-brand-600">chọn file</span>
          </p>
          <p className="text-sm text-gray-500">Excel (.xlsx, .xls) · CSV · TSV · Tối đa 50MB</p>
        </>
      )}
    </div>
  )
}
