import { useState } from 'react'
import { Menu, BarChart3, Settings, X } from 'lucide-react'
import { FileUpload } from './components/FileUpload'
import { ChatPanel } from './components/ChatPanel'
import { SettingsPanel } from './components/SettingsPanel'
import { useAppStore } from './hooks/useStore'
import { Toaster } from 'react-hot-toast'

export default function App() {
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const { error } = useAppStore()

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <Toaster
        position="top-center"
        toastOptions={{
          duration: 3000,
          style: { fontSize: '14px', borderRadius: '12px' },
        }}
      />

      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors lg:hidden"
          >
            <Menu className="w-5 h-5 text-gray-600" />
          </button>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="font-semibold text-gray-900 text-sm">Trợ Lý Phân Tích Số Liệu</h1>
              <p className="text-xs text-gray-500">AI Business Analyst</p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setSettingsOpen(true)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Cài đặt"
          >
            <Settings className="w-5 h-5 text-gray-500" />
          </button>
        </div>
      </header>

      {error && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-2 flex items-center justify-between">
          <p className="text-sm text-red-700">{error}</p>
          <button onClick={() => useAppStore.getState().setError(null)} className="p-1 hover:bg-red-100 rounded">
            <X className="w-4 h-4 text-red-500" />
          </button>
        </div>
      )}

      <div className="flex-1 flex overflow-hidden">
        {sidebarOpen && (
          <aside className="w-80 border-r border-gray-200 bg-white shrink-0 hidden lg:block overflow-y-auto">
            <div className="p-4">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                📁 Dữ liệu
              </p>
              <FileUpload />
            </div>
          </aside>
        )}

        <main className="flex-1 flex flex-col min-w-0 bg-white lg:bg-gray-50">
          {!sidebarOpen && (
            <div className="lg:hidden p-4 border-b border-gray-200 bg-white">
              <FileUpload />
            </div>
          )}
          <ChatPanel />
        </main>
      </div>

      <SettingsPanel isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  )
}
