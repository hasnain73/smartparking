import { useState, useEffect, useRef, useCallback } from 'react'
import ParkMap from './Parkmap.jsx'
import { API_BASE } from './api'

// ─── Mock data for demo (when backend is not running) ──────────────────────
const MOCK_SPOTS = [
  {
    id: 1, latitude: 12.3661, longitude: 76.6880,
    address: 'Mysore Palace Area',
    parking_type: 'street',
    display_label: 'Likely Free',
    confidence_score: 0.87,
    distance: 42,
  },
  {
    id: 2, latitude: 12.3680, longitude: 76.6900,
    address: 'Agrahara Main Road',
    parking_type: 'private',
    display_label: 'Uncertain',
    confidence_score: 0.54,
    distance: 180,
  },
  {
    id: 3, latitude: 12.3650, longitude: 76.6870,
    address: 'Jayanagar 4th Block',
    parking_type: 'private',
    spot_type: 'structured',
    display_label: 'Likely Occupied',
    confidence_score: 0.21,
    distance: 310,
  },
  {
    id: 4, latitude: 12.3675, longitude: 76.6850,
    address: 'K.R. Circle',
    parking_type: 'street',
    display_label: 'Likely Free',
    confidence_score: 0.91,
    distance: 95,
  },
  {
    id: 5, latitude: 12.3690, longitude: 76.6920,
    address: 'Lashkar Mohalla',
    parking_type: 'street',
    display_label: 'Uncertain',
    confidence_score: 0.48,
    distance: 260,
  },
]

const ACCENT_COLORS = [
  { key: 'cherry', color: '#e63946', label: 'Cherry' },
  { key: 'cyan', color: '#06b6d4', label: 'Cyan' },
  { key: 'yellow', color: '#f59e0b', label: 'Amber' },
  { key: 'orange', color: '#f97316', label: 'Orange' },
]

const HEAT_ZONES = [
  { lat: 12.9716, lng: 77.5946, radius: 300, intensity: 0.9 },
  { lat: 12.9352, lng: 77.6245, radius: 250, intensity: 0.7 },
  { lat: 12.9279, lng: 77.6271, radius: 200, intensity: 0.6 }
]

export default function App() {
  const [theme, setTheme] = useState('dark')
  const [accent, setAccent] = useState('cherry')
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef(null)

  const [address, setAddress] = useState('Mysore, Karnataka')
  const [userLocation, setUserLocation] = useState({
    lat: 12.3661,
    lng: 76.688065
  })
  const [radius, setRadius] = useState('5000')

  const [spots, setSpots] = useState([])
  const [loading, setLoading] = useState(false)
  const [loadBar, setLoadBar] = useState(false)
  const [error, setError] = useState(null)
  const [spotCount, setSpotCount] = useState(null)

  // NEW: Destination and heuristic state
  const [destination, setDestination] = useState(null)
  const [availabilityInfo, setAvailabilityInfo] = useState(null)
  const [locLoading, setLocLoading] = useState(false)

  // NEW: Image upload state
  const [selectedFile, setSelectedFile] = useState(null)
  const [selectedType, setSelectedType] = useState('street')
  const [postModalOpen, setPostModalOpen] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState(null)
  const [searchHistory, setSearchHistory] = useState(() => {
    return JSON.parse(localStorage.getItem('parker_history') || '[]')
  })
  const [activeFilters, setActiveFilters] = useState(['street', 'private', 'structured'])
  const fileInputRef = useRef(null)

  // Apply theme & accent to <html>
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    document.documentElement.setAttribute('data-accent', accent)
  }, [theme, accent])

  // Close menu on outside click
  useEffect(() => {
    const handler = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const fetchSpots = useCallback(async (latVal, lngVal, radiusVal) => {
    setLoading(true)
    setLoadBar(true)
    setError(null)

    setTimeout(() => setLoadBar(false), 1200)

    try {
      const url = `${API_BASE}/api/v1/spots/nearby?lat=${latVal}&lng=${lngVal}&radius=${radiusVal}`
      const res = await fetch(url)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      const rawList = Array.isArray(data) ? data : data.spots || data.results || []
      
      // Fake subtle variation for real-time feel
      const list = rawList.map(s => {
        const noise = (Math.random() - 0.5) * 0.05
        let newConf = (s.confidence_score || 0.5) + noise
        newConf = Math.max(0, Math.min(1, newConf))
        return {
          ...s,
          confidence_score: parseFloat(newConf.toFixed(2))
        }
      })

      setSpots(list)
      setSpotCount(list.length)
    } catch (err) {
      // Fallback to mock with variation
      console.warn('Backend unavailable, using mock data')
      const mocked = MOCK_SPOTS.map(s => {
        const noise = (Math.random() - 0.5) * 0.05
        let newConf = (s.confidence_score || 0.5) + noise
        newConf = Math.max(0, Math.min(1, newConf))
        return { ...s, confidence_score: parseFloat(newConf.toFixed(2)) }
      })
      setSpots(mocked)
      setSpotCount(mocked.length)
    } finally {
      setLoading(false)
    }
  }, [])

  // Update search history
  const addToHistory = (query) => {
    const updated = [query, ...searchHistory.filter(h => h !== query)].slice(0, 5)
    setSearchHistory(updated)
    localStorage.setItem('parker_history', JSON.stringify(updated))
  }

  // Filter spots based on active types
  const filteredSpots = spots.filter(s => activeFilters.includes(s.parking_type?.toLowerCase() || 'street'))

  // Auto-fetch on load + hydrate location from cache
  useEffect(() => {
    const cached = localStorage.getItem('parker_last_loc')
    if (cached) {
      try {
        const { lat: cLat, lng: cLng } = JSON.parse(cached)
        setUserLocation({ lat: cLat, lng: cLng })
        fetchSpots(cLat, cLng, radius)
        return
      } catch (e) {
        console.error("Cache error", e)
      }
    }
    fetchSpots(userLocation.lat, userLocation.lng, radius)
  }, [])

  // Auto-refresh every 8 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchSpots(userLocation.lat, userLocation.lng, radius)
    }, 8000)
    return () => clearInterval(interval)
  }, [userLocation.lat, userLocation.lng, radius, fetchSpots])

  // Geolocation helper with Reverse Geocoding
  const handleUseMyLocation = () => {
    if (!('geolocation' in navigator)) {
      alert("Geolocation not supported by this browser.")
      return
    }

    setLocLoading(true)
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const newLat = pos.coords.latitude
        const newLng = pos.coords.longitude
        
        console.log("GPS Location Received:", newLat, newLng)

        // 1. Update coordinates state
        const loc = { lat: newLat, lng: newLng }
        setUserLocation(loc)
        localStorage.setItem('parker_last_loc', JSON.stringify(loc))
        
        // 2. Fetch spots around this location
        fetchSpots(newLat, newLng, radius)

        // 3. Reverse geocoding (Connect GPS to human-readable address)
        try {
          const res = await fetch(
            `https://nominatim.openstreetmap.org/reverse?lat=${newLat}&lon=${newLng}&format=json`
          )
          const data = await res.json()

          if (data && data.display_name) {
            setAddress(data.display_name)
          }
        } catch (err) {
          console.error("Reverse geocode failed", err)
        } finally {
          setLocLoading(false)
        }
      },
      (err) => {
        console.error("Location error", err)
        alert("Location permission denied or unavailable.")
        setLocLoading(false)
      },
      { enableHighAccuracy: true, timeout: 10000 }
    )
  }

  const handleFind = async () => {
    if (!address.trim()) {
      // If address is empty, just use the manual coordinates
      await fetchSpots(userLocation.lat, userLocation.lng, radius)
      return
    }

    setLoading(true)
    setLoadBar(true)
    setError(null)

    try {
      const geoRes = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}`)
      const geoData = await geoRes.json()

      if (!geoData || geoData.length === 0) {
        throw new Error('Address not found. Try a different search.')
      }

      const newLat = parseFloat(geoData[0].lat)
      const newLng = parseFloat(geoData[0].lon)

      setUserLocation({ lat: newLat, lng: newLng })
      addToHistory(address)

      await fetchSpots(newLat, newLng, radius)
    } catch (err) {
      setError(err.message)
      setLoading(false)
      setLoadBar(false)
    }
  }

  // NEW: Handle image upload and CV detection
  const handlePostSpot = async () => {
    if (!selectedFile) {
      alert('Please select an image first')
      return
    }

    setUploading(true)
    setUploadResult(null)

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)
      formData.append('parking_type', selectedType)

      // Use first spot ID if available, otherwise detection-only
      const spotId = spots.length > 0 ? spots[0].id : null
      if (spotId) {
        formData.append('spot_id', spotId)
      }

      const res = await fetch(`${API_BASE}/api/v1/spots/detect`, {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || `HTTP ${res.status}`)
      }

      const result = await res.json()
      setUploadResult(result)

      // Success cleanup
      setSelectedFile(null)
      setPostModalOpen(false)
      
      // Optionally refresh spots to see new signal
      if (result.signal_id) {
        setTimeout(() => fetchSpots(lat, lng, radius), 500)
      }

    } catch (err) {
      console.error('Upload failed:', err)
      setError(err.message || 'Upload failed')
      setTimeout(() => setError(null), 3000)
    } finally {
      setUploading(false)
    }
  }

  const calculateDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371e3
    const φ1 = lat1 * Math.PI / 180
    const φ2 = lat2 * Math.PI / 180
    const Δφ = (lat2 - lat1) * Math.PI / 180
    const Δλ = (lon2 - lon1) * Math.PI / 180
    const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
      Math.cos(φ1) * Math.cos(φ2) *
      Math.sin(Δλ / 2) * Math.sin(Δλ / 2)
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
    return R * c
  }

  const updateAvailability = (destLat, destLng) => {
    if (!userLocation) return

    const distM = calculateDistance(userLocation.lat, userLocation.lng, destLat, destLng)
    const etaMin = Math.round(distM / (30000 / 60))

    // Find the spot data to get confidence
    const spot = spots.find(s => s.lat === destLat && s.lng === destLng)
    const confidence = spot ? (spot.confidence_score || 0.5) : 0.5
    const availWindowMin = Math.round(confidence * 20)
    const remainingTime = availWindowMin - etaMin

    let status = "Likely occupied before arrival"
    let statusClass = "occupied"
    if (remainingTime > 5) {
      status = "Safe to go"
      statusClass = "free"
    } else if (remainingTime >= 0) {
      status = "Risky"
      statusClass = "uncertain"
    }

    setAvailabilityInfo({
      eta: etaMin,
      availability: availWindowMin,
      status,
      statusClass
    })
  }

  const onPostLocation = (clickedLat, clickedLng) => {
    setUserLocation({ lat: clickedLat, lng: clickedLng })
    setPostModalOpen(true)
  }

  const onFindLocation = (clickedLat, clickedLng) => {
    setUserLocation({ lat: clickedLat, lng: clickedLng })
    setDestination({ lat: clickedLat, lng: clickedLng })
    updateAvailability(clickedLat, clickedLng)
    fetchSpots(clickedLat, clickedLng, radius)
  }

  const center = [userLocation.lat, userLocation.lng]

  return (
    <div className="app-layout">
      {/* Loading strip */}
      {loadBar && <div className="status-strip" key={Date.now()} />}

      {/* Error toast */}
      {error && <div className="toast" key={error}>{error}</div>}

      {/* ── TOP BAR ───────────────────────────────────── */}
      <header className="topbar">
        <div className="logo">
          <span className="logo-dot" />
          PARK-ĒR
        </div>

        <div className="menu-wrapper" ref={menuRef}>
          <button
            className="hamburger"
            onClick={() => setMenuOpen(o => !o)}
            aria-label="Menu"
          >
            ☰
          </button>

          {menuOpen && (
            <div className="dropdown">
              {/* Theme */}
              <div className="dropdown-section">
                <label>Theme Mode</label>
                <div className="option-row">
                  {['light', 'dark'].map(t => (
                    <button
                      key={t}
                      className={`option-btn ${theme === t ? 'active' : ''}`}
                      onClick={() => setTheme(t)}
                    >
                      {t === 'light' ? '☀ Light' : '🌙 Dark'}
                    </button>
                  ))}
                </div>
              </div>

              {/* Accent */}
              <div className="dropdown-section">
                <label>Accent Color</label>
                <div className="accent-row">
                  {ACCENT_COLORS.map(a => (
                    <button
                      key={a.key}
                      className={`accent-swatch ${accent === a.key ? 'active' : ''}`}
                      title={a.label}
                      style={{ background: a.color }}
                      onClick={() => setAccent(a.key)}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* ── MAP ──────────────────────────────────────── */}
      <ParkMap
        spots={filteredSpots}
        center={center}
        isDark={theme === 'dark'}
        onPostLocation={onPostLocation}
        onFindLocation={onFindLocation}
        userLocation={userLocation}
        destination={destination}
        heatZones={HEAT_ZONES}
      />

      {/* ── RESULT BADGE ─────────────────────────────── */}
      {spotCount !== null && (
        <div className="result-badge">
          <span className="badge-dot" />
          {spotCount} spot{spotCount !== 1 ? 's' : ''} nearby
        </div>
      )}

      {/* NEW: Upload result badge */}
      {uploadResult && (
        <div className="result-badge" style={{ top: '100px' }}>
          <span className="badge-dot" />
          Detected: <strong>{uploadResult.status}</strong> ({Math.round(uploadResult.confidence * 100)}% confident)
        </div>
      )}

      {/* NEW: Availability heuristic panel */}
      {availabilityInfo && (
        <div className="result-badge" style={{ top: uploadResult ? '160px' : '100px', width: '220px' }}>
          <div style={{ marginBottom: '8px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '4px' }}>
            <strong>Availability Estimate</strong>
          </div>
          <div style={{ fontSize: '0.85rem', display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>ETA:</span> <span>{availabilityInfo.eta} min</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Expires in:</span> <span>{availabilityInfo.availability} min</span>
            </div>
            <div style={{ 
              marginTop: '4px', 
              padding: '4px 8px', 
              borderRadius: '4px', 
              textAlign: 'center',
              fontWeight: 'bold',
              fontSize: '0.8rem',
              background: availabilityInfo.statusClass === 'free' ? '#22c55e33' : 
                          availabilityInfo.statusClass === 'uncertain' ? '#f59e0b33' : '#ef444433',
              color: availabilityInfo.statusClass === 'free' ? '#22c55e' : 
                     availabilityInfo.statusClass === 'uncertain' ? '#f59e0b' : '#ef4444',
            }}>
              {availabilityInfo.status}
            </div>
          </div>
        </div>
      )}

      {/* ── MODAL ────────────────────────────────────── */}
      {postModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>Post Parking Spot</h3>
              <button className="close-btn" onClick={() => setPostModalOpen(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="input-group">
                <span>Upload Image</span>
                <input 
                  type="file" 
                  accept="image/*" 
                  onChange={(e) => setSelectedFile(e.target.files[0])} 
                />
              </div>
              <div className="input-group">
                <span>Parking Type</span>
                <select value={selectedType} onChange={(e) => setSelectedType(e.target.value)}>
                  <option value="street">Street</option>
                  <option value="private">Private</option>
                  <option value="structured">Structured</option>
                </select>
              </div>
              <button 
                className={`btn-primary ${uploading ? 'loading' : ''}`}
                onClick={handlePostSpot}
                disabled={uploading || !selectedFile}
                style={{ width: '100%', marginTop: '16px' }}
              >
                {uploading ? 'Posting…' : 'Submit Spot'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── LEGEND ────────────────────────────────────── */}
      <div className="legend">
        <div style={{ fontSize: '0.65rem', fontWeight: 800, marginBottom: '4px', opacity: 0.6 }}>PARKING TYPES</div>
        {[
          { color: '#FFD700', label: 'Structured' },
          { color: '#3b82f6', label: 'Private' },
          { color: '#ef4444', label: 'Street' },
        ].map(item => (
          <div className="legend-item" key={item.label}>
            <span className="legend-dot" style={{ background: item.color }} />
            {item.label}
          </div>
        ))}
        <div style={{ height: '8px' }} />
        <div style={{ fontSize: '0.65rem', fontWeight: 800, marginBottom: '4px', opacity: 0.6 }}>AVAILABILITY</div>
        {[
          { color: '#22c55e', label: 'Likely Free' },
          { color: '#f59e0b', label: 'Uncertain' },
          { color: '#ef4444', label: 'Likely Occupied' },
        ].map(item => (
          <div className="legend-item" key={item.label}>
            <span className="legend-dot" style={{ background: item.color, borderRadius: '2px' }} />
            {item.label}
          </div>
        ))}
      </div>

      {/* ── CONTROL PANEL ────────────────────────────── */}
      <div className="control-panel">
        <div className="input-group" style={{ flex: 1, minWidth: '200px' }}>
          <span>Address</span>
          <input
            type="text"
            value={address}
            onChange={e => setAddress(e.target.value)}
            onFocus={() => {}} // Optional: show history dropdown
            placeholder="Enter an address or landmark..."
          />
          {searchHistory.length > 0 && (
            <div className="search-history-chips">
              {searchHistory.map(h => (
                <button key={h} className="history-chip" onClick={() => {
                  setAddress(h)
                  handleFind()
                }}>{h}</button>
              ))}
            </div>
          )}
        </div>

        <div className="input-group" style={{ flex: 0, minWidth: '150px' }}>
          <span>Filters</span>
          <div className="filter-chips">
            {['street', 'private', 'structured'].map(f => (
              <button 
                key={f}
                className={`filter-chip ${activeFilters.includes(f) ? 'active' : ''}`}
                onClick={() => {
                  setActiveFilters(prev => 
                    prev.includes(f) ? prev.filter(x => x !== f) : [...prev, f]
                  )
                }}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        <div className="input-group" style={{ maxWidth: 100 }}>
          <span>Latitude</span>
          <input
            type="number"
            value={userLocation.lat}
            onChange={e => setUserLocation({ ...userLocation, lat: parseFloat(e.target.value) })}
            step="0.0001"
          />
        </div>

        <div className="input-group" style={{ maxWidth: 100 }}>
          <span>Longitude</span>
          <input
            type="number"
            value={userLocation.lng}
            onChange={e => setUserLocation({ ...userLocation, lng: parseFloat(e.target.value) })}
            step="0.0001"
          />
        </div>

        <div className="panel-divider" />

        <button
          className={`btn-secondary ${locLoading ? 'loading' : ''}`}
          onClick={handleUseMyLocation}
          disabled={locLoading}
          title="Use my current GPS location"
        >
          {locLoading ? <span className="spinner" /> : '📍'}
          {locLoading ? 'Locating…' : 'Me'}
        </button>

        <div className="panel-divider" />

        <button
          className={`btn-primary ${loading ? 'loading' : ''}`}
          onClick={handleFind}
          disabled={loading}
        >
          {loading ? <span className="spinner" /> : '⌖'}
          {loading ? 'Searching…' : 'Find Parking'}
        </button>

        <button
          className="btn-secondary"
          onClick={() => setPostModalOpen(true)}
        >
          ＋ Post Spot
        </button>
      </div>
    </div>
  )
}