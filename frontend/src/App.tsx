import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import PolicyDetail from './pages/PolicyDetail'
import AskCivicLens from './pages/AskCivicLens'
import UploadBill from './pages/UploadBill'
import Dashboard from './pages/Dashboard'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <main className="pt-16">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/policy/:id" element={<PolicyDetail />} />
            <Route path="/ask" element={<AskCivicLens />} />
            <Route path="/upload" element={<UploadBill />} />
            <Route path="/dashboard" element={<Dashboard />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
