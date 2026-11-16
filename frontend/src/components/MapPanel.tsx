import { useEffect, useRef, useState } from 'react';
import * as maplibregl from 'maplibre-gl';
import {
  GeoJSONSource,
  Map,
  Marker,
} from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import mapLibreWorkerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url';
import { MapPin, RotateCcw, Trash2 } from 'lucide-react';
import {
  coordinatesAreIdentical,
  LatLng,
  validateCoordinate,
} from '../utils/coordinates';
import {
  applyProviderToken,
  DEFAULT_BEARING,
  DEFAULT_PITCH,
  DEFAULT_TERRAIN_EXAGGERATION,
  DEFAULT_ZOOM,
  resolveMapEnvironment,
} from '../config/map';
import { removeCheckpoint, reorderCheckpoint } from '../utils/routePlanning';
import { useAppStore } from '../store/appStore';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:5000';
let mapLibreWorkerConfigured = false;

function configureMapLibreWorker() {
  if (mapLibreWorkerConfigured) return;
  maplibregl.setWorkerUrl(mapLibreWorkerUrl);
  mapLibreWorkerConfigured = true;
}

configureMapLibreWorker();

function markerElement(color: string) {
  const element = document.createElement('div');
  element.style.width = '18px';
  element.style.height = '18px';
  element.style.border = '3px solid white';
  element.style.borderRadius = '50%';
  element.style.background = color;
  element.style.boxShadow = '0 0 12px rgba(34, 197, 94, 0.8)';
  return element;
}

interface PointDetails {
  name: string;
  elevation: number | null;
}

function readableLocationName(result: Record<string, unknown>): string {
  const address = result.address as Record<string, unknown> | undefined;
  const candidates = [
    result.display_name,
    address?.tourism,
    address?.amenity,
    address?.road,
    address?.village,
    address?.town,
    address?.city,
    address?.municipality,
    address?.county,
    address?.state,
    address?.country,
  ];
  const name = candidates.find((value): value is string => typeof value === 'string' && value.trim().length > 0);
  return name ?? '';
}

export default function MapPanel() {
  const setTerrainRouteCoordinates = useAppStore((state) => state.setRouteCoordinates);
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<Map | null>(null);
  const startMarkerRef = useRef<Marker | null>(null);
  const destinationMarkerRef = useRef<Marker | null>(null);
  const inspectionMarkerRef = useRef<Marker | null>(null);
  const checkpointMarkerRefs = useRef<Marker[]>([]);
  const [mode, setMode] = useState<'start' | 'destination' | 'checkpoint' | 'inspection'>('start');
  const modeRef = useRef(mode);
  const [start, setStart] = useState<LatLng | null>(null);
  const [destination, setDestination] = useState<LatLng | null>(null);
  const [inspectionPoint, setInspectionPoint] = useState<LatLng | null>(null);
  const [startDetails, setStartDetails] = useState<PointDetails | null>(null);
  const [destinationDetails, setDestinationDetails] = useState<PointDetails | null>(null);
  const [inspectionDetails, setInspectionDetails] = useState<PointDetails | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Array<Record<string, unknown>>>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [features, setFeatures] = useState<GeoJSON.FeatureCollection | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [terrainExaggeration, setTerrainExaggeration] = useState(
    DEFAULT_TERRAIN_EXAGGERATION
  );
  const [algorithm, setAlgorithm] = useState('dijkstra');
  const [preference, setPreference] = useState('shortest');
  const [route, setRoute] = useState<GeoJSON.FeatureCollection | null>(null);
  const [routeLoading, setRouteLoading] = useState(false);
  const [routeStats, setRouteStats] = useState<Record<string, number | string> | null>(null);
  const [routeMode, setRouteMode] = useState<'single' | 'multiple' | 'multi-stop' | 'emergency'>('single');
  const [checkpoints, setCheckpoints] = useState<LatLng[]>([]);
  const [checkpointDetails, setCheckpointDetails] = useState<Array<PointDetails | null>>([]);
  const startValueRef = useRef<LatLng | null>(null);
  const destinationValueRef = useRef<LatLng | null>(null);
  const checkpointValuesRef = useRef<LatLng[]>([]);
  const [alternativeRoutes, setAlternativeRoutes] = useState<GeoJSON.FeatureCollection[]>([]);
  const [alternativeStats, setAlternativeStats] = useState<Record<string, number | string>[]>([]);
  const [selectedAlternative, setSelectedAlternative] = useState(0);
  const [alternativeCount, setAlternativeCount] = useState(3);
  const [dangerPopulation, setDangerPopulation] = useState(500);
  const [shelterCapacity, setShelterCapacity] = useState(800);
  const [emergencyResult, setEmergencyResult] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    modeRef.current = mode;
  }, [mode]);

  useEffect(() => {
    startValueRef.current = start;
  }, [start]);

  useEffect(() => {
    destinationValueRef.current = destination;
  }, [destination]);

  useEffect(() => {
    checkpointValuesRef.current = checkpoints;
  }, [checkpoints]);

  const syncRoute = (map: Map) => {
    const data = route ?? {
      type: 'FeatureCollection',
      features: [],
    };
    const source = map.getSource('selected-route') as GeoJSONSource | undefined;
    if (source) source.setData(data);
  };

  const placePoint = (point: LatLng, kind?: 'start' | 'destination' | 'checkpoint' | 'inspection') => {
    const validationError = validateCoordinate(point);
    if (validationError) {
      setError(validationError);
      return;
    }
    const selectedKind = kind ?? modeRef.current;
    const otherPoint = selectedKind === 'start'
      ? destinationValueRef.current
      : selectedKind === 'destination' ? startValueRef.current : null;
    if (otherPoint && coordinatesAreIdentical(point, otherPoint)) {
      setError('Start and destination cannot be identical.');
      return;
    }
    if (selectedKind === 'checkpoint' && checkpointValuesRef.current.some((checkpoint) => coordinatesAreIdentical(point, checkpoint))) {
      setError('A checkpoint cannot duplicate another selected point.');
      return;
    }
    if (selectedKind === 'checkpoint' && (
      (startValueRef.current && coordinatesAreIdentical(point, startValueRef.current)) ||
      (destinationValueRef.current && coordinatesAreIdentical(point, destinationValueRef.current))
    )) {
      setError('A checkpoint cannot replace or duplicate Start and Destination.');
      return;
    }
    setError('');
    if (selectedKind === 'start') {
      startValueRef.current = point;
      setStart(point);
    } else if (selectedKind === 'destination') {
      destinationValueRef.current = point;
      setDestination(point);
    }
    else if (selectedKind === 'inspection') setInspectionPoint(point);
    else if (selectedKind === 'checkpoint') {
      const nextCheckpoints = [...checkpointValuesRef.current, point];
      checkpointValuesRef.current = nextCheckpoints;
      setCheckpoints(nextCheckpoints);
    }
  };

  const describePoint = async (
    point: LatLng,
    kind: 'start' | 'destination' | 'inspection' | 'checkpoint',
    checkpointIndex?: number
  ) => {
    const details: PointDetails = {
      name: `Unnamed location near ${point.lat.toFixed(4)}, ${point.lng.toFixed(4)}`,
      elevation: null,
    };
    const reverseController = new AbortController();
    const timeout = window.setTimeout(() => reverseController.abort(), 8000);
    try {
      const reverseResponse = await fetch(
        `${API_BASE}/api/reverse-geocode?lat=${point.lat}&lng=${point.lng}`,
        { signal: reverseController.signal }
      );
      const reversePayload = await reverseResponse.json();
      if (reverseResponse.ok) {
        const name = readableLocationName(reversePayload.data ?? {});
        if (name) details.name = name;
      }

      const elevationResponse = await fetch(
        `${API_BASE}/api/elevation?lat=${point.lat}&lng=${point.lng}`,
        { signal: reverseController.signal }
      );
      const elevationPayload = await elevationResponse.json();
      if (elevationResponse.ok) {
        const elevation = Number(elevationPayload.data?.elevation);
        if (Number.isFinite(elevation)) details.elevation = elevation;
      }
    } catch {
      details.name = `Unnamed location near ${point.lat.toFixed(4)}, ${point.lng.toFixed(4)}`;
    } finally {
      window.clearTimeout(timeout);
    }

    if (kind === 'start') setStartDetails(details);
    else if (kind === 'destination') setDestinationDetails(details);
    else if (kind === 'inspection') setInspectionDetails(details);
    else if (checkpointIndex !== undefined) {
      setCheckpointDetails((current) => current.map((item, index) => index === checkpointIndex ? details : item));
    }
  };

  useEffect(() => {
    if (start) void describePoint(start, 'start');
    else setStartDetails(null);
  }, [start]);

  useEffect(() => {
    if (destination) void describePoint(destination, 'destination');
    else setDestinationDetails(null);
  }, [destination]);

  useEffect(() => {
    if (inspectionPoint) void describePoint(inspectionPoint, 'inspection');
    else setInspectionDetails(null);
  }, [inspectionPoint]);

  useEffect(() => {
    setCheckpointDetails((current) => checkpoints.map((_point, index) => {
      const existing = current[index];
      return existing ?? null;
    }));
    checkpoints.forEach((point, index) => void describePoint(point, 'checkpoint', index));
  }, [checkpoints]);

  const searchPlaces = async () => {
    const query = searchQuery.trim();
    if (!query) return;
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 8000);
    setSearchLoading(true);
    setError('');
    try {
      const response = await fetch(
        `${API_BASE}/api/geocode?q=${encodeURIComponent(query)}&limit=5`,
        { signal: controller.signal }
      );
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.message ?? 'Place search failed.');
      setSearchResults(Array.isArray(payload.data) ? payload.data : []);
    } catch (requestError) {
      setSearchResults([]);
      setError(requestError instanceof Error ? requestError.message : 'Place search failed.');
    } finally {
      window.clearTimeout(timeout);
      setSearchLoading(false);
    }
  };

  const chooseSearchResult = (result: Record<string, unknown>) => {
    const lng = Number(result.lon);
    const lat = Number(result.lat);
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
      setError('The search provider returned invalid coordinates.');
      return;
    }
    placePoint({ lat, lng });
    const name = readableLocationName(result);
    const details = { name, elevation: null };
    if (mode === 'start') setStartDetails(details);
    else if (mode === 'destination') setDestinationDetails(details);
    else setInspectionDetails(details);
    setSearchResults([]);
    mapRef.current?.flyTo({ center: [lng, lat], zoom: Math.max(mapRef.current.getZoom(), 10) });
  };

  const reset = () => {
    setStart(null);
    setDestination(null);
    setInspectionPoint(null);
    startValueRef.current = null;
    destinationValueRef.current = null;
    checkpointValuesRef.current = [];
    setError('');
    startMarkerRef.current?.remove();
    destinationMarkerRef.current?.remove();
    inspectionMarkerRef.current?.remove();
    startMarkerRef.current = null;
    destinationMarkerRef.current = null;
    inspectionMarkerRef.current?.remove();
    inspectionMarkerRef.current = null;
    if (mapRef.current) syncRoute(mapRef.current);
    setRoute(null);
    setRouteStats(null);
    setCheckpoints([]);
    setCheckpointDetails([]);
    setTerrainRouteCoordinates([]);
    setAlternativeRoutes([]);
    setAlternativeStats([]);
    setEmergencyResult(null);
    checkpointMarkerRefs.current.forEach((marker) => marker.remove());
    checkpointMarkerRefs.current = [];
    for (let routeIndex = 0; routeIndex < 10; routeIndex += 1) {
      const sourceId = `alternative-route-${routeIndex}`;
      const layerId = `${sourceId}-line`;
      if (mapRef.current?.getLayer(layerId)) mapRef.current.removeLayer(layerId);
      if (mapRef.current?.getSource(sourceId)) mapRef.current.removeSource(sourceId);
    }
  };

  const moveCheckpoint = (index: number, direction: -1 | 1) => {
    setCheckpoints((current) => {
      const next = reorderCheckpoint(current, index, direction);
      checkpointValuesRef.current = next;
      return next;
    });
    setCheckpointDetails((current) => {
      if (index + direction < 0 || index + direction >= current.length) return current;
      const next = [...current];
      [next[index], next[index + direction]] = [next[index + direction], next[index]];
      return next;
    });
  };

  const removeCheckpointAt = (index: number) => {
    setCheckpoints((current) => {
      const next = removeCheckpoint(current, index);
      checkpointValuesRef.current = next;
      return next;
    });
    setCheckpointDetails((current) => current.filter((_details, detailIndex) => detailIndex !== index));
  };

  useEffect(() => {
    const map = mapRef.current;
    if (map && map.getSource('selected-route')) {
      const source = map.getSource('selected-route') as GeoJSONSource;
      source.setData(route ?? { type: 'FeatureCollection', features: [] });
    }
    if (!route) {
      setTerrainRouteCoordinates([]);
      return;
    }
    const coordinates = route.features
      .flatMap((feature) => feature.geometry.type === 'LineString' ? feature.geometry.coordinates : [])
      .filter((coordinate): coordinate is number[] => coordinate.length >= 2)
      .map((coordinate) => ({ lng: coordinate[0], lat: coordinate[1] }));
    setTerrainRouteCoordinates(coordinates);
  }, [route]);

  useEffect(() => {
    if (!start || !destination) {
      setRoute(null);
      setRouteStats(null);
      return;
    }
    if (routeMode !== 'single') return;
    const controller = new AbortController();
    setRouteLoading(true);
    setError('');
    fetch(`${API_BASE}/api/routes/calculate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        start: [start.lng, start.lat],
        destination: [destination.lng, destination.lat],
        stops: checkpoints.map((checkpoint) => [checkpoint.lng, checkpoint.lat]),
        algorithm,
        preference,
      }),
      signal: controller.signal,
    })
      .then(async (response) => {
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.message ?? 'Unable to calculate route.');
        setRoute(payload.data.route);
        setRouteStats(payload.data);
      })
      .catch((requestError: unknown) => {
        if (requestError instanceof DOMException && requestError.name === 'AbortError') return;
        setRoute(null);
        setRouteStats(null);
        setError(requestError instanceof Error ? requestError.message : 'Unable to calculate route.');
      })
      .finally(() => setRouteLoading(false));
    return () => controller.abort();
  }, [start, destination, checkpoints, algorithm, preference, routeMode]);

  const calculateMultiple = async () => {
    if (!start || !destination) {
      setError('Select both start and destination.');
      return;
    }
    const controller = new AbortController();
    setRouteLoading(true);
    setError('');
    setAlternativeRoutes([]);
    try {
      const response = await fetch(`${API_BASE}/api/routes/multiple`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          start: [start.lng, start.lat],
          destination: [destination.lng, destination.lat],
          algorithm,
          preference,
          count: alternativeCount,
        }),
        signal: controller.signal,
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.message ?? 'Unable to calculate alternatives.');
      setAlternativeRoutes(payload.data.routes.map((item: { route: GeoJSON.FeatureCollection }) => item.route));
      setAlternativeStats(payload.data.routes);
      setSelectedAlternative(0);
      setRouteStats(payload.data.routes[0]);
    } catch (requestError) {
      if (requestError instanceof DOMException && requestError.name === 'AbortError') return;
      setError(requestError instanceof Error ? requestError.message : 'Unable to calculate alternatives.');
    } finally {
      setRouteLoading(false);
    }
  };

  const calculateMultiStop = async () => {
    if (!start || !destination) {
      setError('Select both start and destination.');
      return;
    }
    setRouteLoading(true);
    setError('');
    setRoute(null);
    try {
      const response = await fetch(`${API_BASE}/api/routes/multi-stop`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          start: [start.lng, start.lat],
          stops: checkpoints.map((checkpoint) => [checkpoint.lng, checkpoint.lat]),
          destination: [destination.lng, destination.lat],
          preference: preference === 'fastest' ? 'fastest_total_time'
            : preference === 'lowest_elevation' ? 'lowest_total_elevation'
            : preference === 'safest' ? 'safest_total_route'
            : 'shortest_total_distance',
          strategy: 'auto',
        }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.message ?? 'Unable to calculate multi-stop route.');
      setRoute(payload.data.route);
      setRouteStats(payload.data);
      setCheckpoints(payload.data.optimized_stop_order.map((coordinate: [number, number]) => ({
        lng: coordinate[0],
        lat: coordinate[1],
      })));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to calculate multi-stop route.');
    } finally {
      setRouteLoading(false);
    }
  };

  const analyzeEvacuation = async () => {
    if (!start || !destination) {
      setError('Select a danger-zone point and shelter.');
      return;
    }
    setRouteLoading(true);
    setError('');
    setEmergencyResult(null);
    try {
      const response = await fetch(`${API_BASE}/api/evacuation/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dangerZones: [{
            id: 'zone-1',
            location: [start.lng, start.lat],
            population: dangerPopulation,
            severity: 'high',
            priority: 1,
            active: true,
          }],
          shelters: [{
            id: 'shelter-1',
            location: [destination.lng, destination.lat],
            capacity: shelterCapacity,
            active: true,
          }],
          blockedRoads: [],
          floodZones: [],
          preference: 'safest',
          algorithm: 'max_flow',
        }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.message ?? 'Unable to analyze evacuation.');
      setEmergencyResult(payload);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to analyze evacuation.');
    } finally {
      setRouteLoading(false);
    }
  };

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.getSource('terrain-dem')) return;
    for (const routeIndex of [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]) {
      const sourceId = `alternative-route-${routeIndex}`;
      const layerId = `${sourceId}-line`;
      if (!alternativeRoutes[routeIndex]) {
        if (map.getLayer(layerId)) map.removeLayer(layerId);
        if (map.getSource(sourceId)) map.removeSource(sourceId);
        continue;
      }
      const source = map.getSource(sourceId) as GeoJSONSource | undefined;
      if (source) source.setData(alternativeRoutes[routeIndex]);
      else {
        map.addSource(sourceId, { type: 'geojson', data: alternativeRoutes[routeIndex] });
        map.addLayer({
          id: layerId,
          type: 'line',
          source: sourceId,
          paint: {
            'line-color': '#38bdf8',
            'line-width': routeIndex === selectedAlternative ? 5 : 3,
            'line-opacity': routeIndex === selectedAlternative ? 1 : 0.8,
          },
        });
      }
      map.setPaintProperty(
        layerId,
        'line-color',
        routeIndex === selectedAlternative ? '#22c55e' : ['#38bdf8', '#a78bfa', '#f59e0b'][routeIndex % 3]
      );
      map.setPaintProperty(layerId, 'line-width', routeIndex === selectedAlternative ? 5 : 3);
    }
  }, [alternativeRoutes, selectedAlternative]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !emergencyResult) return;
    const routes = (emergencyResult.routes ?? []) as Array<{ route: GeoJSON.FeatureCollection }>;
    const sourceId = 'emergency-routes';
    const collection: GeoJSON.FeatureCollection = {
      type: 'FeatureCollection',
      features: routes.flatMap((item) => item.route.features),
    };
    const source = map.getSource(sourceId) as GeoJSONSource | undefined;
    if (source) source.setData(collection);
    else {
      map.addSource(sourceId, { type: 'geojson', data: collection });
      map.addLayer({
        id: `${sourceId}-line`,
        type: 'line',
        source: sourceId,
        paint: {
          'line-color': '#f97316',
          'line-width': 5,
          'line-opacity': 0.95,
        },
      });
    }
  }, [emergencyResult]);

  const resetView = () => {
    mapRef.current?.easeTo({
      center: [86.925, 27.9881],
      zoom: DEFAULT_ZOOM,
      pitch: DEFAULT_PITCH,
      bearing: DEFAULT_BEARING,
      duration: 800,
    });
  };

  const fitRoute = () => {
    const map = mapRef.current;
    if (!map || !start || !destination) return;
    const bounds = new maplibregl.LngLatBounds(start, start);
    bounds.extend(destination);
    map.fitBounds(bounds, { padding: 90, pitch: DEFAULT_PITCH, duration: 800 });
  };

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    let mapEnvironment;
    try {
      mapEnvironment = resolveMapEnvironment();
      if (!mapEnvironment.styleUrl || !mapEnvironment.terrainSourceUrl) {
        throw new Error('Map style URL and terrain source URL are required.');
      }
    } catch (configError) {
      setError(
        configError instanceof Error
          ? configError.message
          : 'Map configuration is invalid.'
      );
      return;
    }

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: applyProviderToken(mapEnvironment.styleUrl, mapEnvironment.providerToken),
      center: [86.925, 27.9881],
      zoom: DEFAULT_ZOOM,
      pitch: DEFAULT_PITCH,
      bearing: DEFAULT_BEARING,
      minZoom: 3,
      maxPitch: 85,
      attributionControl: {},
    });
    mapRef.current = map;

    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right');
    map.on('error', (event: { error?: unknown }) => {
      setError(event.error instanceof Error ? event.error.message : 'Map rendering failed.');
    });

    map.on('click', (event: maplibregl.MapMouseEvent) =>
      placePoint({ lat: event.lngLat.lat, lng: event.lngLat.lng })
    );
    map.once('load', () => {
      try {
        map.addSource('terrain-dem', {
          type: 'raster-dem',
          tiles: [
            applyProviderToken(
              mapEnvironment.terrainSourceUrl,
              mapEnvironment.providerToken
            ),
          ],
          tileSize: 256,
          encoding: 'terrarium',
          attribution: 'Terrain tiles: AWS Terrain Tiles / Mapzen; elevation data derived from SRTM.',
        });
        map.setTerrain({
          source: 'terrain-dem',
          exaggeration: DEFAULT_TERRAIN_EXAGGERATION,
        });
        map.addSource('selected-route', {
          type: 'geojson',
          data: { type: 'FeatureCollection', features: [] },
        });
        map.addLayer({
          id: 'hillshade',
          type: 'hillshade',
          source: 'terrain-dem',
          paint: {
            'hillshade-shadow-color': '#0c0a09',
            'hillshade-highlight-color': '#4ade80',
            'hillshade-exaggeration': 0.45,
          },
        });
        map.addLayer({
          id: 'selected-route-line',
          type: 'line',
          source: 'selected-route',
          paint: {
            'line-color': '#ef4444',
            'line-width': 4,
            'line-opacity': 0.95,
          },
        });
        syncRoute(map);
      } catch (terrainError) {
        setError(
          terrainError instanceof Error
            ? terrainError.message
            : 'Unable to initialize terrain.'
        );
      }
    });

    return () => {
      startMarkerRef.current?.remove();
      destinationMarkerRef.current?.remove();
      inspectionMarkerRef.current?.remove();
      checkpointMarkerRefs.current.forEach((marker) => marker.remove());
      checkpointMarkerRefs.current = [];
      startMarkerRef.current = null;
      destinationMarkerRef.current = null;
      inspectionMarkerRef.current = null;
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (map.getSource('terrain-dem')) {
      map.setTerrain({ source: 'terrain-dem', exaggeration: terrainExaggeration });
    }
  }, [terrainExaggeration]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.getStyle()) return;
    syncRoute(map);

    const updateMarker = (
      current: Marker | null,
      point: LatLng | null,
      kind: 'start' | 'destination',
      color: string
    ) => {
      if (!point) {
        current?.remove();
        return null;
      }
      if (current) {
        current.setLngLat([point.lng, point.lat]);
        return current;
      }
      const marker = new maplibregl.Marker({
        element: markerElement(color),
        draggable: true,
      })
        .setLngLat([point.lng, point.lat])
        .addTo(map);
      marker.on('dragend', () => {
        const position = marker.getLngLat();
        placePoint({ lat: position.lat, lng: position.lng }, kind);
      });
      return marker;
    };

    startMarkerRef.current = updateMarker(
      startMarkerRef.current,
      start,
      'start',
      '#22c55e'
    );
    destinationMarkerRef.current = updateMarker(
      destinationMarkerRef.current,
      destination,
      'destination',
      '#ef4444'
    );
    if (!inspectionPoint) {
      inspectionMarkerRef.current?.remove();
      inspectionMarkerRef.current = null;
    } else if (inspectionMarkerRef.current) {
      inspectionMarkerRef.current.setLngLat([inspectionPoint.lng, inspectionPoint.lat]);
    } else {
      inspectionMarkerRef.current = new maplibregl.Marker({
        element: markerElement('#38bdf8'),
        draggable: true,
      }).setLngLat([inspectionPoint.lng, inspectionPoint.lat]).addTo(map);
      inspectionMarkerRef.current.on('dragend', () => {
        const position = inspectionMarkerRef.current?.getLngLat();
        if (position) placePoint({ lat: position.lat, lng: position.lng }, 'inspection');
      });
    }
    checkpointMarkerRefs.current.forEach((marker) => marker.remove());
    checkpointMarkerRefs.current = checkpoints.map((checkpoint, index) => {
      const marker = new maplibregl.Marker({
        element: markerElement('#38bdf8'),
        draggable: true,
      }).setLngLat([checkpoint.lng, checkpoint.lat]).addTo(map);
      marker.getElement().title = `Checkpoint ${index + 1}: ${checkpoint.lat.toFixed(5)}, ${checkpoint.lng.toFixed(5)}`;
      marker.on('dragend', () => {
        const position = marker.getLngLat();
        setCheckpoints((current) => current.map((point, pointIndex) =>
          pointIndex === index ? { lat: position.lat, lng: position.lng } : point
        ));
        void describePoint({ lat: position.lat, lng: position.lng }, 'checkpoint', index);
      });
      return marker;
    });
  }, [start, destination, inspectionPoint, checkpoints, loading]);

  useEffect(() => {
    const bounds = { south: 27.85, west: 86.85, north: 28.15, east: 87.15 };
    const controller = new AbortController();
    setLoading(true);
    setError('');
    fetch(
      `${API_BASE}/api/map/features?south=${bounds.south}&west=${bounds.west}&north=${bounds.north}&east=${bounds.east}`,
      { signal: controller.signal }
    )
      .then(async (response) => {
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.message ?? 'Unable to load map features.');
        setFeatures(payload.data);
      })
      .catch((requestError: unknown) => {
        if (requestError instanceof DOMException && requestError.name === 'AbortError') return;
        setError(requestError instanceof Error ? requestError.message : 'Unable to load map features.');
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !features) return;
    const addFeatures = () => {
      const existing = map.getSource('osm-features') as GeoJSONSource | undefined;
      if (existing) existing.setData(features);
      else {
        map.addSource('osm-features', { type: 'geojson', data: features });
        map.addLayer({
          id: 'osm-roads',
          type: 'line',
          source: 'osm-features',
          paint: { 'line-color': '#f59e0b', 'line-width': 1.5, 'line-opacity': 0.85 },
        });
      }
    };
    if (map.loaded()) addFeatures();
    else map.once('load', addFeatures);
  }, [features]);

  return (
    <section className="absolute bottom-3 left-3 right-3 h-[58%] z-[500] border border-stone-700 bg-stone-950 shadow-2xl">
      <div className="h-10 px-3 flex items-center justify-between border-b border-stone-800">
        <div className="flex items-center gap-2 text-xs font-bold text-stone-300">
          <MapPin size={14} className="text-green-500" />
          TERRAIN-AWARE ROUTE OPTIMIZER
        </div>
        <div className="flex gap-2 items-center">
          <button onClick={() => setMode('start')} className={`px-2 py-1 text-xs rounded ${mode === 'start' ? 'bg-green-800 text-white' : 'bg-stone-800 text-stone-400'}`}>Start</button>
          <button onClick={() => setMode('destination')} className={`px-2 py-1 text-xs rounded ${mode === 'destination' ? 'bg-red-800 text-white' : 'bg-stone-800 text-stone-400'}`}>Destination</button>
          <button onClick={() => setMode('checkpoint')} className={`px-2 py-1 text-xs rounded ${mode === 'checkpoint' ? 'bg-blue-800 text-white' : 'bg-stone-800 text-stone-400'}`}>Checkpoint</button>
          <button onClick={() => setMode('inspection')} className={`px-2 py-1 text-xs rounded ${mode === 'inspection' ? 'bg-sky-800 text-white' : 'bg-stone-800 text-stone-400'}`}>Inspection point</button>
          <button onClick={resetView} title="Reset camera" className="p-1 text-stone-400 hover:text-green-400"><RotateCcw size={15} /></button>
          <button onClick={reset} title="Clear selections" className="p-1 text-stone-400 hover:text-white"><Trash2 size={15} /></button>
        </div>
      </div>
      <div className="absolute left-3 top-14 z-[1000] w-80 rounded border border-stone-700 bg-stone-950/95 p-3 shadow-xl">
        <form onSubmit={(event) => { event.preventDefault(); void searchPlaces(); }} className="flex gap-2">
          <input
            aria-label="Search a place"
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Search place or landmark"
            className="min-w-0 flex-1 rounded border border-stone-700 bg-stone-900 px-2 py-1.5 text-xs text-stone-200"
          />
          <button type="submit" disabled={searchLoading} className="rounded bg-green-700 px-2 text-xs font-bold text-white">
            {searchLoading ? '...' : 'Search'}
          </button>
        </form>
        {searchResults.map((result, index) => (
          <button
            key={`${String(result.place_id ?? index)}-${index}`}
            onClick={() => chooseSearchResult(result)}
            className="mt-1 block w-full rounded px-2 py-1 text-left text-xs text-stone-300 hover:bg-stone-800"
          >
            {readableLocationName(result) || 'Unnamed search result'}
          </button>
        ))}
        {[
          ['Start', start, startDetails],
          ['Destination', destination, destinationDetails],
          ['Inspection', inspectionPoint, inspectionDetails],
        ].map(([label, point, details]) => (
          point ? (
            <div key={String(label)} className="mt-2 border-t border-stone-800 pt-2 text-[11px]">
              <b className="text-green-400">{String(label)}</b>
              <div className="text-stone-200">{details ? (details as PointDetails).name : 'Resolving name...'}</div>
              <div className="text-stone-500">
                {(point as LatLng).lat.toFixed(5)}, {(point as LatLng).lng.toFixed(5)}
                {details && (details as PointDetails).elevation !== null ? ` · ${(details as PointDetails).elevation?.toFixed(0)} m` : ''}
              </div>
            </div>
          ) : null
        ))}
        {checkpoints.length > 0 && (
          <div className="mt-2 border-t border-stone-800 pt-2 text-[11px]">
            <b className="text-sky-400">Checkpoints</b>
            {checkpoints.map((point, index) => (
              <div key={`${point.lat}-${point.lng}-${index}`} className="mt-1 flex items-start justify-between gap-2">
                <div>
                  <span className="text-stone-300">{index + 1}. {checkpointDetails[index]?.name ?? 'Resolving name...'}</span>
                  <div className="text-stone-500">
                    {point.lat.toFixed(5)}, {point.lng.toFixed(5)}
                    {checkpointDetails[index]?.elevation !== null && checkpointDetails[index]?.elevation !== undefined
                      ? ` · ${checkpointDetails[index]?.elevation?.toFixed(0)} m`
                      : ''}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      <div className="absolute right-3 top-12 z-[1000] flex items-center gap-2 rounded bg-stone-950/95 px-2 py-1 text-[10px] border border-stone-700">
        <label htmlFor="terrain-exaggeration">Elevation</label>
        <input
          id="terrain-exaggeration"
          type="range"
          min="0.5"
          max="2.5"
          step="0.05"
          value={terrainExaggeration}
          onChange={(event) => setTerrainExaggeration(Number(event.target.value))}
          className="accent-green-500"
        />
        <span>{terrainExaggeration.toFixed(2)}x</span>
      </div>
      <div className="absolute left-[340px] top-14 z-[1000] flex gap-2 rounded bg-stone-950/95 px-2 py-1 text-[10px] border border-stone-700">
        <select aria-label="Route mode" value={routeMode} onChange={(event) => setRouteMode(event.target.value as 'single' | 'multiple' | 'multi-stop' | 'emergency')} className="hidden bg-stone-900 text-stone-200">
          <option value="single">Single route</option>
          <option value="multiple">Alternatives</option>
          <option value="multi-stop">Multi-stop</option>
          <option value="emergency">Emergency evacuation</option>
        </select>
        <select aria-label="Route algorithm" value={algorithm} onChange={(event) => setAlgorithm(event.target.value)} className="bg-stone-900 text-stone-200">
          <option value="dijkstra">Dijkstra</option>
          <option value="astar">A*</option>
        </select>
        <select aria-label="Route preference" value={preference} onChange={(event) => setPreference(event.target.value)} className="bg-stone-900 text-stone-200">
          <option value="shortest">Shortest</option>
          <option value="fastest">Fastest</option>
          <option value="easiest">Easiest</option>
          <option value="lowest_elevation">Lowest elevation</option>
          <option value="safest">Safest</option>
        </select>
        {routeMode === 'multiple' && (
          <select aria-label="Alternative count" value={alternativeCount} onChange={(event) => setAlternativeCount(Number(event.target.value))} className="bg-stone-900 text-stone-200">
            {[1, 2, 3, 4, 5].map((count) => <option key={count} value={count}>{count} routes</option>)}
          </select>
        )}
        {routeMode === 'emergency' && (
          <>
            <label>Population <input aria-label="Danger zone population" type="number" min="1" value={dangerPopulation} onChange={(event) => setDangerPopulation(Math.max(1, Number(event.target.value)))} className="w-16 bg-stone-900 text-stone-200" /></label>
            <label>Capacity <input aria-label="Shelter capacity" type="number" min="0" value={shelterCapacity} onChange={(event) => setShelterCapacity(Math.max(0, Number(event.target.value)))} className="w-16 bg-stone-900 text-stone-200" /></label>
            <button onClick={analyzeEvacuation} className="rounded bg-orange-700 px-2 font-bold text-white">Analyze</button>
          </>
        )}
        {routeMode !== 'single' && (
          <button onClick={routeMode === 'multiple' ? calculateMultiple : calculateMultiStop} className="rounded bg-green-700 px-2 font-bold text-white">Calculate</button>
        )}
      </div>
      <div ref={containerRef} className="h-[calc(100%-2.5rem)] w-full bg-stone-900" />
      {(loading || error) && (
        <div className="absolute top-12 left-3 z-[1000] rounded bg-stone-950/95 px-3 py-2 text-xs border border-stone-700">
          {loading ? 'Loading OpenStreetMap features...' : <span className="text-red-300">{error}</span>}
        </div>
      )}
      {routeLoading && <div className="absolute bottom-12 left-3 z-[1000] rounded bg-stone-950/95 px-3 py-2 text-xs">Calculating route...</div>}
      {routeStats && (
        <div className="absolute bottom-12 right-3 z-[1000] grid grid-cols-2 gap-x-4 gap-y-1 rounded bg-stone-950/95 px-3 py-2 text-[10px] text-stone-200 border border-stone-700">
          <span>Distance: {(Number(routeStats.distance) / 1000).toFixed(2)} km</span>
          <span>Time: {Math.round(Number(routeStats.estimated_time) / 60)} min</span>
          <span>Elevation gain: {Math.round(Number(routeStats.elevation_gain))} m</span>
          <span>Max slope: {Number(routeStats.maximum_slope).toFixed(1)}%</span>
          <span>Difficulty: {Number(routeStats.terrain_difficulty).toFixed(1)}/10</span>
          <span>Explored: {String(routeStats.nodes_explored)} nodes</span>
          <span className="col-span-2">Execution: {Number(routeStats.execution_time).toFixed(2)} ms</span>
        </div>
      )}
      {alternativeRoutes.length > 0 && (
        <div className="absolute bottom-12 left-1/3 z-[1000] flex gap-1 rounded bg-stone-950/95 p-1">
          {alternativeRoutes.map((_, index) => (
            <button
              key={index}
              onClick={() => {
                setSelectedAlternative(index);
                setRouteStats(alternativeStats[index] ?? null);
              }}
              className={`px-2 py-1 text-[10px] rounded ${selectedAlternative === index ? 'bg-green-700 text-white' : 'bg-stone-800 text-stone-300'}`}
            >
              {index === 0 ? 'Recommended' : `Route ${index + 1}`}
            </button>
          ))}
        </div>
      )}
      {checkpoints.length > 0 && (
        <div className="absolute top-24 right-3 z-[1000] max-w-72 rounded bg-stone-950/95 p-2 text-[10px] text-stone-200">
          {checkpoints.map((checkpoint, index) => (
            <div key={`${checkpoint.lat}-${checkpoint.lng}-${index}`} className="flex items-center gap-1 border-b border-stone-800 py-1">
              <span className="flex-1">
                <b>Checkpoint {index + 1}</b>: {checkpointDetails[index]?.name ?? 'Resolving name...'}<br />
                {checkpoint.lat.toFixed(5)}, {checkpoint.lng.toFixed(5)}
                {checkpointDetails[index]?.elevation !== null && checkpointDetails[index]?.elevation !== undefined ? ` · ${checkpointDetails[index]?.elevation?.toFixed(0)} m` : ''}
              </span>
              <button onClick={() => moveCheckpoint(index, -1)} aria-label={`Move checkpoint ${index + 1} up`}>↑</button>
              <button onClick={() => moveCheckpoint(index, 1)} aria-label={`Move checkpoint ${index + 1} down`}>↓</button>
              <button onClick={() => removeCheckpointAt(index)} aria-label={`Remove checkpoint ${index + 1}`}>×</button>
            </div>
          ))}
        </div>
      )}
      {emergencyResult && (
        <div className="absolute bottom-12 right-3 z-[1000] grid grid-cols-2 gap-x-3 rounded border border-orange-700 bg-stone-950/95 px-3 py-2 text-[10px] text-stone-200">
          <span>Population: {String((emergencyResult.summary as Record<string, unknown>).totalPopulation)}</span>
          <span>Evacuated: {String((emergencyResult.summary as Record<string, unknown>).evacuatedPopulation)}</span>
          <span>Unmet: {String((emergencyResult.summary as Record<string, unknown>).unmetPopulation)}</span>
          <span>Coverage: {String((emergencyResult.summary as Record<string, unknown>).evacuationPercentage)}%</span>
          <span className="col-span-2">Warnings: {String((emergencyResult.warnings as unknown[]).length)}</span>
        </div>
      )}
      {start && destination && (
        <button onClick={fitRoute} className="absolute bottom-3 right-3 z-[1000] rounded bg-green-800 px-3 py-2 text-xs font-bold text-white shadow">FIT SELECTIONS</button>
      )}
    </section>
  );
}
