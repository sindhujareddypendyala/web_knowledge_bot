import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Navbar from './components/layout/Navbar/Navbar.jsx'
import Footer from './components/layout/Footer/Footer.jsx'
import FloatingAssistant from './components/FloatingAssistant/FloatingAssistant.jsx'
import Home from './pages/Home.jsx'
import Documentation from './pages/Documentation.jsx'
import Tutorials from './pages/Tutorials.jsx'
import APIReference from './pages/APIReference.jsx'
import Guides from './pages/Guides.jsx'
import FAQ from './pages/FAQ.jsx'
import { ThemeProvider } from './hooks/ThemeProvider.jsx'

function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <div className="app-shell">
          <Navbar />
          <main>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/documentation" element={<Documentation />} />
              <Route path="/api-reference" element={<APIReference />} />
              <Route path="/sdk" element={<Guides sdkOnly />} />
              <Route path="/tutorials" element={<Tutorials />} />
              <Route path="/guides" element={<Guides />} />
              <Route path="/faq" element={<FAQ />} />
            </Routes>
          </main>
          <Footer />
          <FloatingAssistant />
        </div>
      </BrowserRouter>
    </ThemeProvider>
  )
}

export default App
