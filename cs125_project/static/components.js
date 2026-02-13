/**
  Defines interactive elements, manages behavior,
  and dictates how data is displayed
**/

const { useState, useEffect, useRef } = React;

const Sidebar = ({ restaurants, onSearch, isLoading }) => {
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
    <div className = "w-1/3 max-w-sm h-full bg-white border-r border-gray-300 shadow-xl z-10 flex flex-col">
      <div className = "p-4 border-b border-gray-200 bg-white sticky top-0 z-20">
        <h1 className = "text-2xl font-bold text-gray-800">Restaurant Recommender</h1>
        
        <form onSubmit={handleSearch} className = "relative mt-4">
          <div className = "absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg className = "h-5 w-5 text-gray-400" fill = "none" stroke = "currentColor" viewBox = "0 0 24 24">
              <path strokeLinecap = "round" strokeLineJoin = "round" strokeWidth = "2" d = "M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>

          <input
            type = "text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            className = "block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-gray-50 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-black focus:border-black sm:text-sm transition duration-150"
            placeholder = "e.g., cheap vegan restaurants near Irvine"
            disabled={isLoading}
          />
        </form>
        
        {isLoading ? (
          <p className = "text-sm text-gray-500 mt-3">Searching...</p>
        ) : (
          <p className = "text-sm text-gray-500 mt-3">{restaurants.length} result(s) {searchQuery ? 'found' : 'nearby'}</p>
        )}
      </div>

      <div className = "flex-1 overflow-y-auto p-2 space-y-2">
        {restaurants.map((r) => (
          <div 
            key={r.id} 
            className = "p-3 bg-white border border-gray-100 rounded-lg hover:shadow-md hover:bg-gray-50 cursor-pointer transition-all duration-200"
          >
            <div className = "flex justify-between items-start">
              <div>
                <h3 className = "font-bold text-gray-900">{r.name}</h3>
                <p className = "text-xs text-gray-500 mt-1">{r.type}</p>
              </div>
              <span className = "bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded-full font-medium">
                {r.rating} ★
              </span>
            </div>
            <div className = "mt-2 flex items-center text-sm text-gray-600">
              <span className = "font-medium text-green-700">{r.price}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const MapView = ({ restaurants }) => {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const MAPBOX_TOKEN = "pk.eyJ1IjoiYWJpZ290IiwiYSI6ImNtbDNoZ2ZrejB0cnYzZnB4aGVkcDI4b2MifQ.s6M_2fu2bxR1Oz6XXC-PqA";

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

    return () => mapRef.current.remove();
  }, []);

  useEffect(() => {
    if (!mapRef.current || !restaurants || restaurants.length === 0) return;

    // clear existing markers
    const currentMarkers = document.getElementsByClassName('marker');
    while(currentMarkers[0]) {
      currentMarkers[0].parentNode.removeChild(currentMarkers[0]);
    }

    // Calculate center of all restaurants
    const avgLat = restaurants.reduce((sum, r) => sum + (r.lat || 0), 0) / restaurants.length;
    const avgLng = restaurants.reduce((sum, r) => sum + (r.lng || 0), 0) / restaurants.length;
    
    // Center map on results
    if (restaurants.length > 0) {
      mapRef.current.flyTo({
        center: [avgLng, avgLat],
        zoom: 13,
        duration: 1000
      });
    }

    restaurants.forEach(r => {
      if (!r.lat || !r.lng) return; // Skip if coordinates missing
      
      const el = document.createElement('div');
      el.className = 'marker';

      const rating = r.rating || 0;
      const price = r.price || '$';
      const type = r.type || 'Restaurant';
      const image = r.image || 'https://images.adsttc.com/media/images/5e4c/1025/6ee6/7e0b/9d00/0877/newsletter/feature_-_Main_hall_1.jpg?1582043123';

      const popupHTML = `
        <div class="w-60 overflow-hidden font-sans bg-white shadow-lg">
          <div class="h-32 w-full bg-cover bg-center" style="background-image: url('${image}')"></div>
          <div class="p-4">
            <h3 class="font-bold text-lg text-gray-900">${r.name || 'Unknown'}</h3>
            <div class="flex items-center text-sm text-gray-500 mt-1">
              <span class="text-yellow-500 font-bold mr-1">★ ${rating.toFixed(1)}</span>
              <span>• ${price} • ${type}</span>
            </div>
            ${r.vicinity ? `<p class="text-xs text-gray-400 mt-2">${r.vicinity}</p>` : ''}
            <button class="mt-4 w-full bg-gray-900 text-white py-2 rounded-lg hover:bg-black transition text-sm">View Details</button>
          </div>
        </div>
      `;

      new mapboxgl.Marker(el)
        .setLngLat([r.lng, r.lat])
        .setPopup(new mapboxgl.Popup({ offset: 25, closeButton: false }).setHTML(popupHTML))
        .addTo(mapRef.current);
    });
  }, [restaurants]);

  return <div ref={mapContainerRef} className="w-full h-full" />;
};

const App = () => {
  const [restaurants, setRestaurants] = useState(TEST_RESTAURANTS);
  const [isLoading, setIsLoading] = useState(false);
  const [userLocation, setUserLocation] = useState(null);

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
          setUserLocation({ lat: 33.6846, lng: -117.8265 });
        }
      );
    } else {
      // Default to Irvine if geolocation not supported
      setUserLocation({ lat: 33.6846, lng: -117.8265 });
    }
  }, []);

  const handleSearch = async (query) => {
    if (!query.trim()) return;

    setIsLoading(true);
    try {
      // Prepare request data
      const requestData = {
        query: query,
      };

      // Add user location if available
      if (userLocation) {
        requestData.lat = userLocation.lat;
        requestData.lng = userLocation.lng;
      }

      // Make API call
      const response = await fetch('/api/restaurants/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to fetch restaurants');
      }

      const data = await response.json();
      
      // Format restaurants for display
      const formattedRestaurants = data.restaurants.map(r => ({
        ...r,
        image: r.image || 'https://images.adsttc.com/media/images/5e4c/1025/6ee6/7e0b/9d00/0877/newsletter/feature_-_Main_hall_1.jpg?1582043123'
      }));

      setRestaurants(formattedRestaurants);
    } catch (error) {
      console.error('Error fetching restaurants:', error);
      alert('Error: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };


  return (
    <div className="flex w-full h-full relative overflow-hidden">
      <Sidebar 
        restaurants={restaurants} 
        onSearch={handleSearch}
        isLoading={isLoading}
      />

      <div className = "flex-1 relative">
        <MapView restaurants={restaurants} />
      </div>
    </div>
  );
};