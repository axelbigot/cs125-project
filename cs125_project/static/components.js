/**
  Defines interactive elements, manages behavior,
  and dictates how data is displayed
**/

const { useState, useEffect, useRef } = React;

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
        <div class="w-64 overflow-hidden font-sans bg-white shadow-lg">
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
    <div className="w-full h-full relative">
      <MapView restaurants={TEST_RESTAURANTS} />
    </div>
  );
};