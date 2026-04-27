import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

function getStatusColor(spot) {
  if (spot.spot_type === "structured") return "#a855f7" // purple
  if (spot.parking_type === "private") return "#FFD700"  // gold
  return "#ef4444" // red (street default)
}

function getStatusClass(label) {
  if (!label) return ''
  const l = label.toLowerCase()
  if (l.includes('free') || l.includes('available')) return 'free'
  if (l.includes('uncertain') || l.includes('maybe')) return 'uncertain'
  return 'occupied'
}

function makeIcon(color, isHighConfidence = false) {
  const size = isHighConfidence ? [32, 40] : [28, 36]
  const anchor = isHighConfidence ? [16, 40] : [14, 36]

  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="${size[0]}" height="${size[1]}" viewBox="0 0 28 36">
      <filter id="s" x="-50%" y="-50%" width="200%" height="200%">
        <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="${color}" flood-opacity="0.5"/>
      </filter>
      <path filter="url(#s)" d="M14 0C6.27 0 0 6.27 0 14c0 9.33 14 22 14 22S28 23.33 28 14C28 6.27 21.73 0 14 0z"
        fill="${color}" />
      <circle cx="14" cy="14" r="6" fill="white" opacity="0.9">
        ${isHighConfidence ? '<animate attributeName="r" values="5;7;5" dur="1.5s" repeatCount="indefinite" />' : ''}
      </circle>
    </svg>
  `
  return L.divIcon({
    html: svg,
    className: '',
    iconSize: size,
    iconAnchor: anchor,
    popupAnchor: [0, -size[1]],
  })
}

function buildPopupHTML(spot) {
  const color = getStatusColor(spot)
  const cls = getStatusClass(spot.display_label)
  const conf = Math.round((spot.confidence_score || 0) * 100)

  return `
    <div class="popup-card">
      <div class="popup-label ${cls}">${spot.display_label || 'Unknown'}</div>
      <div class="popup-rows">
        <div class="popup-row">
          <span class="key">Address</span>
          <span class="val">${spot.address || '—'}</span>
        </div>
        <div class="popup-row">
          <span class="key">Type</span>
          <span class="val">${spot.parking_type || '—'}</span>
        </div>
        <div class="popup-row">
          <span class="key">Distance</span>
          <span class="val">${spot.distance_m ? spot.distance_m + ' m' : '—'}</span>
        </div>
        <div class="popup-row">
          <span class="key">Confidence</span>
          <span class="val">${conf}%</span>
        </div>
      </div>
      <div class="confidence-bar-wrap">
        <div class="confidence-bar" style="width:${conf}%; background:${color};"></div>
      </div>
    </div>
  `
}

export default function ParkMap({ spots, center, isDark, onPostLocation, onFindLocation, userLocation, destination, heatZones }) {
  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const markersRef = useRef([])
  const heatZonesRef = useRef([])
  const tileLayerRef = useRef(null)
  const userMarkerRef = useRef(null)
  const routeRef = useRef(null)
  const [selectedLocation, setSelectedLocation] = useState(null)
  const callbacksRef = useRef({ onPostLocation, onFindLocation })

  useEffect(() => {
    callbacksRef.current = { onPostLocation, onFindLocation }
  }, [onPostLocation, onFindLocation])

  // Init map
  useEffect(() => {
    if (mapInstanceRef.current) return
    mapInstanceRef.current = L.map(mapRef.current, {
      center: center,
      zoom: 15,
      zoomControl: false,
    })

    L.control.zoom({ position: 'topright' }).addTo(mapInstanceRef.current)

    tileLayerRef.current = L.tileLayer(
      'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      { attribution: '© OpenStreetMap', maxZoom: 19 }
    ).addTo(mapInstanceRef.current)

    mapInstanceRef.current.on('click', (e) => {
      const { lat, lng } = e.latlng
      setSelectedLocation({ lat, lng })

      const container = L.DomUtil.create('div')
      container.innerHTML = `
                <div>
                  <p style="margin: 0 0 10px 0; font-weight: 500; color: #111;">What do you want to do?</p>
                  <div style="display: flex; gap: 8px;">
                    <button id="post-btn" style="cursor: pointer; padding: 6px 12px; background: #e63946; color: white; border: none; border-radius: 4px; font-weight: 600;">Post Spot</button>
                    <button id="find-btn" style="cursor: pointer; padding: 6px 12px; background: #3b82f6; color: white; border: none; border-radius: 4px; font-weight: 600;">Find Parking</button>
                  </div>
                </div>
            `

      container.querySelector('#post-btn').onclick = () => {
        mapInstanceRef.current.closePopup()
        if (callbacksRef.current.onPostLocation) {
          callbacksRef.current.onPostLocation(lat, lng)
        }
      }

      container.querySelector('#find-btn').onclick = () => {
        mapInstanceRef.current.closePopup()
        if (callbacksRef.current.onFindLocation) {
          callbacksRef.current.onFindLocation(lat, lng)
        }
      }

      L.popup()
        .setLatLng([lat, lng])
        .setContent(container)
        .openOn(mapInstanceRef.current)
    })

    return () => {
      mapInstanceRef.current?.remove()
      mapInstanceRef.current = null
    }
  }, [])

  // Recenter
  useEffect(() => {
    if (!mapInstanceRef.current) return
    mapInstanceRef.current.setView(center, 15, { animate: true })
  }, [center[0], center[1]])

  // Update markers
  useEffect(() => {
    if (!mapInstanceRef.current) return
    markersRef.current.forEach(m => m.remove())
    markersRef.current = []

    spots.forEach(spot => {
      if (!spot.lat || !spot.lng) return
      const color = getStatusColor(spot)
      const isHighConf = (spot.confidence_score || 0) > 0.8
      const icon = makeIcon(color, isHighConf)
      const marker = L.marker([spot.lat, spot.lng], { icon })
        .addTo(mapInstanceRef.current)
        .bindPopup(buildPopupHTML(spot), {
          maxWidth: 240,
          className: '',
        })
      markersRef.current.push(marker)
    })
  }, [spots])

  // Update user location marker
  useEffect(() => {
    if (!mapInstanceRef.current || !userLocation) return
    
    if (userMarkerRef.current) {
      userMarkerRef.current.remove()
    }
    
    userMarkerRef.current = L.circleMarker([userLocation.lat, userLocation.lng], {
      radius: 8,
      color: '#3b82f6',
      fillColor: '#3b82f6',
      fillOpacity: 0.9
    }).addTo(mapInstanceRef.current)
  }, [userLocation])

  // Draw route from user to destination
  useEffect(() => {
    if (!userLocation || !destination || !mapInstanceRef.current) return

    const fetchRoute = async () => {
      const url = `https://router.project-osrm.org/route/v1/driving/${userLocation.lng},${userLocation.lat};${destination.lng},${destination.lat}?overview=full&geometries=geojson`
      try {
        const res = await fetch(url)
        const data = await res.json()
        if (!data.routes || data.routes.length === 0) return

        const coords = data.routes[0].geometry.coordinates
        const latlngs = coords.map(c => [c[1], c[0]])

        if (routeRef.current) {
          mapInstanceRef.current.removeLayer(routeRef.current)
        }

        routeRef.current = L.polyline(latlngs, {
          color: '#3b82f6',
          weight: 5
        }).addTo(mapInstanceRef.current)
      } catch (err) {
        console.error("Routing error:", err)
      }
    }

    fetchRoute()
  }, [userLocation, destination])

  // Draw heat zones
  useEffect(() => {
    if (!mapInstanceRef.current || !heatZones) return
    
    heatZonesRef.current.forEach(z => z.remove())
    heatZonesRef.current = []

    heatZones.forEach(zone => {
      const circle = L.circle([zone.lat, zone.lng], {
        radius: zone.radius,
        color: "#f97316",
        fillColor: "#f97316",
        fillOpacity: zone.intensity * 0.3
      })
      .addTo(mapInstanceRef.current)
      .bindPopup("High demand area")
      
      heatZonesRef.current.push(circle)
    })
  }, [heatZones])

  return (
    <div className="map-container">
      <div ref={mapRef} style={{ width: '100%', height: '100%' }} />
    </div>
  )
}