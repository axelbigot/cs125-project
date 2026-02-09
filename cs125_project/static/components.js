/**
  Defines interactive elements, manages behavior,
  and dictates how data is displayed
**/

const { useState, useEffect, useRef } = React;

const Sidebar = ({ restaurants }) => {
  return (
    <div className = "w-1/3 max-w-sm h-full bg-white border-r border-gray-300 shadow-xl z-10 flex flex-col">
      <div className = "p-4 border-b border-gray-200 bg-white sticky top-0 z-20">
        <h1 className = "text-2xl font-bold text-gray-800">Restaurant Recommender</h1>
        
        <div className = "relative mt-4">
          <div className = "absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg className = "h-5 w-5 text-gray-400" fill = "none" stroke = "currentColor" viewBox = "0 0 24 24">
              <path strokeLinecap = "round" strokeLineJoin = "round" strokeWidth = "2" d = "M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>

          <input
            type = "text"
            className = "block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-gray-50 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-black focus:border-black sm:text-sm transition duration-150"
            placeholder = "Search"
          />
        </div>
        
        <p className = "text-sm text-gray-500 mt-3">{restaurants.length} result(s) nearby</p>
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
    if (!mapRef.current) return;

    // clear existing markers
    const currentMarkers = document.getElementsByClassName('marker');
    while(currentMarkers[0]) {
      currentMarkers[0].parentNode.removeChild(currentMarkers[0]);
    }

    restaurants.forEach(r => {
      const el = document.createElement('div');
      el.className = 'marker';

      const popupHTML = `
        <div class="w-60 overflow-hidden font-sans bg-white shadow-lg">
          <div class="h-32 w-full bg-cover bg-center" style="background-image: url('${r.image}')"></div>
          <div class="p-4">
            <h3 class="font-bold text-lg text-gray-900">${r.name}</h3>
            <div class="flex items-center text-sm text-gray-500 mt-1">
              <span class="text-yellow-500 font-bold mr-1">★ ${r.rating}</span>
              <span>• ${r.price} • ${r.type}</span>
            </div>
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
  return (
    <div className="flex w-full h-full relative overflow-hidden">
      <Sidebar restaurants = {TEST_RESTAURANTS} />

      <div className = "flex-1 relative">
        <MapView restaurants = {TEST_RESTAURANTS} />
      </div>
    </div>
  );
};