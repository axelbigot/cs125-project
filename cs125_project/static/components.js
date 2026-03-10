/**
  Defines interactive elements, manages behavior,
  and dictates how data is displayed
**/

const { useState, useEffect, useRef } = React;

const MAPBOX_TOKEN = "pk.eyJ1IjoiYWJpZ290IiwiYSI6ImNtbDNoZ2ZrejB0cnYzZnB4aGVkcDI4b2MifQ.s6M_2fu2bxR1Oz6XXC-PqA";
const DEFAULT_IMAGE_URL = "https://images.adsttc.com/media/images/5e4c/1025/6ee6/7e0b/9d00/0877/newsletter/feature_-_Main_hall_1.jpg?1582043123";
const DEFAULT_LOCATION = { lat: 33.6846, lng: -117.8265 };

const getCookie = (name) => {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
};

const ensureCsrfCookie = async () => {
  // Hitting this endpoint sets csrftoken cookie (and returns a token).
  try {
    await fetch('/api/csrf/', { credentials: 'same-origin' });
  } catch (e) {
    // ignore
  }
};

const apiFetch = async (url, options = {}) => {
  const method = (options.method || 'GET').toUpperCase();
  const headers = { ...(options.headers || {}) };

  if (method !== 'GET' && method !== 'HEAD') {
    await ensureCsrfCookie();
    const csrf = getCookie('csrftoken');
    if (csrf) headers['X-CSRFToken'] = csrf;
  }

  return fetch(url, {
    credentials: 'same-origin',
    ...options,
    headers,
  });
};

/* START PAGE */
const StartPage = ({ isOpen, onClose, onSave, onSignUpClick, initialPrefs, isLoggedIn }) => {
  
  // Initialize user preferences
  const [prefs, setPrefs] = useState(initialPrefs || {
    dietary: [],
    maxPrice: 4,
    minRating: 0,
    adventurousness: 'Balanced'
  });

  if (!isOpen) return null;

  // Toggles numeric thresholds values
  const handleThresholdToggle = (field, value) => {
    setPrefs(prev => ({
      ...prev,
      [field]: prev[field] === value ? 0 : value
    }));
  };

  // Toggles dietary requirements
  const handleDietaryToggle = (diet) => {
    setPrefs(prev => ({
      ...prev,
      dietary: prev.dietary.includes(diet) 
        ? prev.dietary.filter(d => d !== diet) 
        : [...prev.dietary, diet]
    }));
  };

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 overflow-hidden">
        
        {/* Header Section */}
        <div className="flex justify-between items-center mb-1">
          <h2 className="text-2xl font-black tracking-tight uppercase">Welcome</h2>
          
          <button 
            onClick={isLoggedIn ? null : onSignUpClick} 
            disabled={isLoggedIn} 
            className={`font-black tracking-widest uppercase px-4 py-1 rounded-xl transition-colors mt-2 ${
              isLoggedIn 
                ? 'bg-gray-100 text-gray-400 cursor-default' 
                : 'bg-black text-white hover:bg-gray-800'   
            }`}
          >
            {isLoggedIn ? 'Logged In' : 'Sign Up'}
          </button>
        </div>

        <h4 className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-6">Enter your preferences</h4>

        {/* Dietary Selection */}
        <div className="mb-6">
          <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">Dietary Needs</label>
          <div className="flex flex-wrap gap-2">
            {['Vegetarian', 'Vegan', 'Gluten-Free'].map(diet => (
              <button
                key={diet}
                onClick={() => handleDietaryToggle(diet)}
                className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${
                  prefs.dietary.includes(diet) 
                    ? 'bg-black text-white' 
                    : 'bg-gray-100 text-black hover:bg-gray-200'
                }`}
              >
                {diet}
              </button>
            ))}
          </div>
        </div>

        {/* Max Price */}
        <div className="mb-6">
          <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">Max Price Level</label>
          <div className="flex gap-2">
            {[1, 2, 3, 4].map(price => (
              <button
                key={price}
                onClick={() => handleThresholdToggle('maxPrice', price)}
                className={`flex-1 py-2 rounded-lg font-bold transition-all ${
                  prefs.maxPrice >= price ? 'bg-black text-white' : 'bg-gray-100 text-gray-400'
                }`}
              >
                {'$'.repeat(price)}
              </button>
            ))}
          </div>
        </div>
        
        {/* Min Rating */}
        <div className="mb-6">
          <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">Min Ratings</label>
          <div className="flex gap-2">
            {[1, 2, 3, 4, 5].map(star => (
              <button
                key={star}
                onClick={() => handleThresholdToggle('minRating', star)}
                className={`flex-1 py-2 rounded-lg font-bold transition-all ${
                  prefs.minRating >= star ? 'bg-black text-white' : 'bg-gray-100 text-gray-400'
                }`}
              >
                ★
              </button>
            ))}
          </div>
        </div>

        {/* Adventurousness */}
        <div className="mb-6">
          <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">Adventurousness</label>
          <div className="flex gap-2">
            {['Safe', 'Balanced', 'Experimental'].map((level) => (
              <button
                key={level}
                type="button"
                onClick={() => setPrefs({ ...prefs, adventurousness: level })}
                className={`flex-1 py-3 rounded-lg text-xs font-black uppercase tracking-wider transition-all ${
                  prefs.adventurousness === level
                    ? 'bg-black text-white'
                    : 'bg-gray-100 text-gray-400 hover:bg-gray-200'
                }`}
              >
                {level}
              </button>
            ))}
          </div>
        </div>

        {/* Submit Button */}
        <button 
          onClick={() => {
            onSave(prefs);
            onClose();
          }}
          className="w-full bg-black text-white font-black tracking-widest uppercase py-4 rounded-xl hover:bg-gray-800 transition-colors mt-4"
        >
          Submit
        </button>
      </div>
    </div>
  );
}

/* SIGN UP PAGE */
const SignUpPage = ({ isOpen, onClose, onSignUp }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    // TODO: Implement actual database connection/authentication here
    console.log('add to database (to be implemented):', { email, password });
   
    onSignUp({ email, password });
    onClose();
  };  

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[60] flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8 relative overflow-hidden">
        
        {/* Close Button */}
        <button 
          onClick={onClose}
          className="absolute top-6 right-6 text-gray-400 hover:text-black transition-colors">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <h2 className="text-2xl font-black tracking-tight uppercase mb-2">Create Account or Login</h2>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Email Address</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 bg-gray-50 border border-transparent rounded-xl text-sm font-medium focus:outline-none focus:bg-white focus:border-black transition-all"
              placeholder="JohnRestaurant@gmail.com"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 bg-gray-50 border border-transparent rounded-xl text-sm font-medium focus:outline-none focus:bg-white focus:border-black transition-all"
              placeholder="••••••••"
            />
          </div>

          <button 
            type="submit"
            className="w-full bg-black text-white font-black tracking-widest uppercase py-4 rounded-xl hover:bg-gray-800 transition-colors mt-4"
          >
            Create Account
          </button>
        </form>
      </div>
    </div>
  );
}

/* SIDEBAR */
const Sidebar = ({ restaurants, onSearch, isLoading, selectedId, onSelect }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [inputValue, setInputValue] = useState('');

  const handleSearch = (e) => {
    e.preventDefault();
    if (inputValue.trim()) {
      setSearchQuery(inputValue.trim());
      onSearch(inputValue.trim());
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch(e);
    }
  };

  return (
    <div className="w-1/3 max-w-sm h-full bg-white border-r border-gray-200 shadow-[20px_0_40px_rgba(0,0,0,0.05)] z-10 flex flex-col">
      
      {/* Search Header */}
      <div className="p-6 border-b border-gray-100 bg-white sticky top-0 z-20">
        <h1 className="text-2xl font-black text-black tracking-tighter uppercase">Restaurant</h1>
        <h1 className="text-2xl font-black text-black tracking-tighter uppercase">Recommender</h1>
        
        <form onSubmit={handleSearch} className="relative mt-6">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLineJoin="round" strokeWidth="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            className="block w-full pl-11 pr-4 py-3 bg-gray-50 border border-transparent rounded-xl text-sm font-medium text-black placeholder-gray-400 focus:outline-none focus:bg-white focus:border-black focus:ring-1 focus:ring-black transition-all duration-200"
            placeholder="Search"
            disabled={isLoading}
          />
        </form>
        
        <p className="text-xs font-bold text-gray-400 mt-4 uppercase tracking-widest">
            {restaurants.length} {'Results'}
        </p>
      </div>

      {/* Restaurant List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {restaurants.map((r) => (
          <div 
            key={r.id} 
            onClick={() => onSelect(r.id)}
            className={`p-4 rounded-2xl cursor-pointer transition-all duration-300 ${
              selectedId === r.id 
                ? 'bg-black text-white shadow-xl transform scale-[1.02]' 
                : 'bg-white border border-gray-100 text-black hover:border-gray-300 hover:shadow-md'
            }`}
          >
            <div className="flex justify-between items-start">
              <div className="pr-4">
                <h3 className={`font-black text-lg leading-tight tracking-tight ${selectedId === r.id ? 'text-white' : 'text-black'}`}>
                    {r.name}
                </h3>
                <p className={`text-xs mt-1.5 font-medium ${selectedId === r.id ? 'text-gray-400' : 'text-gray-500'}`}>
                  {r.vicinity}
                </p>
              </div>
              <span className={`flex-shrink-0 text-xs px-2.5 py-1 rounded-md font-bold ${
                selectedId === r.id ? 'bg-white text-black' : 'bg-gray-200 text-black'
              }`}>
                {r.rating} ★
              </span>
            </div>
            <div className="mt-4 flex items-center text-sm">
              <span className={`font-bold px-2 py-1 rounded bg-transparent ${selectedId === r.id ? 'text-white' : 'text-black'}`}>
                {r.price}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

/* MAP VIEW */
const MapView = ({ restaurants, selectedId }) => {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const markersRef = useRef({});

  // Initialize Mapbox
  useEffect(() => {
    mapboxgl.accessToken = MAPBOX_TOKEN;
    mapRef.current = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: "mapbox://styles/mapbox/light-v11",
      center: [-117.8428, 33.6459],
      zoom: 14,
      pitch: 45,
    });

    mapRef.current.on('load', () => mapRef.current.resize());
    mapRef.current.addControl(new mapboxgl.NavigationControl(), 'bottom-right');

    // Cleanup map instance
    return () => mapRef.current.remove();
  }, []);

  // Update map markers when restaurants array is modified
  useEffect(() => {
    if (!mapRef.current || !restaurants || restaurants.length === 0) return;

    // Clear existing DOM markers
    const currentMarkers = document.getElementsByClassName('marker');
    while(currentMarkers[0]) {
      currentMarkers[0].parentNode.removeChild(currentMarkers[0]);
    }

    // Clear marker instances from ref
    Object.values(markersRef.current).forEach(marker => marker.remove());
    markersRef.current = {};

    // Calculate center of all restaurants
    const avgLat = restaurants.reduce((sum, r) => sum + (r.lat || 0), 0) / restaurants.length;
    const avgLng = restaurants.reduce((sum, r) => sum + (r.lng || 0), 0) / restaurants.length;
    
    // Center map on results
    if (restaurants.length > 0) {
      mapRef.current.flyTo({
        center: [avgLng, avgLat],
        duration: 500,
        zoom: 14,
        pitch: 45,
      });
    }

    // Generate new markers and popups
    restaurants.forEach(r => {
      if (!r.lat || !r.lng) return; // Skip if coordinates missing
      
      const el = document.createElement('div');
      el.className = 'marker';

      const rating = r.rating || 0;
      const price = r.price || '$';
      const type = r.type || 'Restaurant';
      const image = r.image || 'https://images.adsttc.com/media/images/5e4c/1025/6ee6/7e0b/9d00/0877/newsletter/feature_-_Main_hall_1.jpg?1582043123';

      const popupHTML = `
        <div class="w-64 overflow-hidden font-sans bg-white">
          <div class="h-40 w-full bg-cover bg-center relative" style="background-image: url('${image}')">
            <div class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
          </div>
          <div class="p-5">
            <h3 class="font-black text-xl text-black tracking-tight leading-tight">${r.name || 'Unknown'}</h3>
            <div class="flex items-center text-sm mt-3">
              <span class="bg-black text-white px-2 py-0.5 rounded text-xs font-bold mr-2">★ ${rating.toFixed(1)}</span>
              <span class="text-gray-500 font-bold">${price} </span>
            </div>
            ${r.vicinity ? `<p class="text-xs text-gray-400 mt-3 font-medium uppercase tracking-wider">${r.vicinity}</p>` : ''}
            <button class="mt-5 w-full bg-black text-white font-black tracking-widest uppercase py-3 rounded-lg hover:bg-gray-800 transition-colors text-xs">View Details</button>
          </div>
        </div>
      `;

      const popup = new mapboxgl.Popup({ offset: 25, closeButton: true }).setHTML(popupHTML);
      const marker = new mapboxgl.Marker(el)
        .setLngLat([r.lng, r.lat])
        .setPopup(popup)
        .addTo(mapRef.current);

      markersRef.current[r.id] = marker;
    });
  }, [restaurants]);

  // Handle selecting popup for specific restaurant in sidebar
  useEffect(() => {
    if (!mapRef.current || !selectedId || !restaurants.length) return;

    const selectedData = restaurants.find(r => r.id === selectedId);
    const selectedMarker = markersRef.current[selectedId];

    // Close any open popus
    Object.values(markersRef.current).forEach(marker => {
      const p = marker.getPopup();
      if (p && p.isOpen()) p.remove(); 
    });

    if (selectedData) {
      mapRef.current.flyTo({
        center: [selectedData.lng, selectedData.lat],
        zoom: 16, 
        pitch: 60, 
        duration: 1500, 
        essential: true
      });
    }

    // Open target marker popup
    if (selectedMarker) {
      const popup = selectedMarker.getPopup();
      if (!popup.isOpen()) {
        selectedMarker.togglePopup();
      }
    }
  }, [selectedId, restaurants]);

  return <div ref={mapContainerRef} className="w-full h-full" />;
};



/* MAIN APP */
const App = () => {
  const [restaurants, setRestaurants] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [userLocation, setUserLocation] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [showStartPage, setShowStartPage] = useState(true);
  const [showSignUp, setShowSignUp] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const [userPrefs, setUserPrefs] = useState({
    dietary: [],
    maxPrice: 4, 
    minRating: 0,
    adventurousness: 'Balanced'
  })

  // Load preferences (backend if logged in, else localStorage/session)
  useEffect(() => {
    const loadPrefs = async () => {
      // Fast path: localStorage (for instant UI)
      try {
        const raw = localStorage.getItem('userPrefs');
        if (raw) setUserPrefs(JSON.parse(raw));
      } catch (e) {
        // ignore
      }

      // Backend path: session or authenticated prefs
      try {
        const resp = await apiFetch('/api/preferences/', { method: 'GET' });
        if (resp.ok) {
          const data = await resp.json();
          if (data?.preferences) setUserPrefs(data.preferences);
          setIsLoggedIn(!!data?.authenticated);
        }
      } catch (e) {
        // ignore
      }
    };

    loadPrefs();
  }, []);

  // Get user's current location on mount
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setUserLocation({
            lat: position.coords.latitude,
            lng: position.coords.longitude
          });
        },
        (error) => {
          console.log('Geolocation error:', error);
          
          // Default to Irvine if geolocation fails
          setUserLocation(DEFAULT_LOCATION);
        }
      );
    } else {

      // Default to Irvine if geolocation not supported
      setUserLocation(DEFAULT_LOCATION);
    }
  }, []);

  // API call to fetch restaurants on search query
  const handleSearch = async (query) => {
    if (!query.trim()) return;
    setIsLoading(true);
    
    try {
      // Prepare request data
      const enhancedQuery = userPrefs.dietary.length > 0 
        ? `${query} ${userPrefs.dietary.join(' ')}` 
        : query;

      // Make API call
      const response = await fetch('/api/restaurants/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: enhancedQuery,
          lat: userLocation?.lat,
          lng: userLocation?.lng,
          preferences: {
            dietary: userPrefs.dietary,
            max_price: userPrefs.maxPrice,
            min_rating: userPrefs.minRating,
            adventurousness: userPrefs.adventurousness
          }
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to fetch restaurants');
      }

      const data = await response.json();
      
      // Format restaurants for display
      const formattedRestaurants = data.restaurants.map(r => ({
        ...r,
        image: r.image || DEFAULT_IMAGE_URL
      }));

      setRestaurants(formattedRestaurants);
    } catch (error) {
      console.error('Error fetching restaurants:', error);
      alert('Error: ' + error.message);
    } finally {
      setIsLoading(false);
    }

    setSelectedId(null);
  };

  return (
    <div className="flex w-full h-full relative overflow-hidden">
      <StartPage 
        isOpen={showStartPage} 
        initialPrefs={userPrefs}
        isLoggedIn={isLoggedIn}
        onClose={() => setShowStartPage(false)} 
        onSignUpClick={() => {
          setShowSignUp(true);
        }}
        onSave={async (prefs) => {
          setUserPrefs(prefs);
          try {
            localStorage.setItem('userPrefs', JSON.stringify(prefs));
          } catch (e) {
            // ignore
          }
          try {
            await apiFetch('/api/preferences/', {
              method: 'PUT',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(prefs),
            });
          } catch (e) {
            // ignore
          }
          // After saving preferences, immediately fetch recommendations
          // using a generic query so the user doesn't land on an empty state.
          try {
            await handleSearch('restaurants');
          } catch (e) {
            // ignore
          }
        }} 
      />
      
      <SignUpPage 
        isOpen={showSignUp}
        onClose={() => {
          setShowSignUp(false)
          setShowStartPage(true);
        }}
        onSignUp={async (data) => {
          // Try login first; if it fails, try signup.
          let authed = false;
          try {
            const loginResp = await apiFetch('/api/auth/login/', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(data),
            });
            authed = loginResp.ok;
          } catch (e) {
            // ignore
          }

          if (!authed) {
            try {
              const signupResp = await apiFetch('/api/auth/signup/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
              });
              authed = signupResp.ok;
            } catch (e) {
              // ignore
            }
          }

          if (authed) {
            setIsLoggedIn(true);
            // Persist current prefs to the logged-in user profile
            try {
              await apiFetch('/api/preferences/', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(userPrefs),
              });
            } catch (e) {
              // ignore
            }
          } else {
            alert('Login/Signup failed. Check your email/password.');
          }

          setShowSignUp(false);
          setShowStartPage(true);
        }}
      />

      <Sidebar 
        restaurants={restaurants} 
        onSearch={handleSearch}
        isLoading={isLoading}
        selectedId={selectedId}
        onSelect={setSelectedId}
      />

      <div className = "flex-1 relative">
        <MapView 
          restaurants={restaurants} 
          selectedId={selectedId}
        />
      </div>
    </div>
  );
};