import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { ApiError, createRideRequest } from "../services/api";

export function CreateRidePage() {
  const { token } = useAuth();
  const navigate = useNavigate();

  const [pickupAddress, setPickupAddress] = useState("");
  const [pickupLat, setPickupLat] = useState("");
  const [pickupLng, setPickupLng] = useState("");
  const [destinationAddress, setDestinationAddress] = useState("");
  const [destinationLat, setDestinationLat] = useState("");
  const [destinationLng, setDestinationLng] = useState("");
  const [departureTime, setDepartureTime] = useState("");
  const [timeFlexibility, setTimeFlexibility] = useState(20);
  const [passengerCount, setPassengerCount] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setError(null);
    setIsSubmitting(true);
    try {
      await createRideRequest(token, {
        pickup_address: pickupAddress,
        pickup: { latitude: Number(pickupLat), longitude: Number(pickupLng) },
        destination_address: destinationAddress,
        destination: { latitude: Number(destinationLat), longitude: Number(destinationLng) },
        departure_time: new Date(departureTime).toISOString(),
        time_flexibility_minutes: timeFlexibility,
        passenger_count: passengerCount,
      });
      navigate("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create ride request");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="ride-form">
      <h1>Find a Ride</h1>
      <p className="form-hint">
        Map search isn't wired up yet — enter coordinates manually for now (e.g. from Google Maps "copy
        coordinates").
      </p>
      <form onSubmit={handleSubmit}>
        <fieldset>
          <legend>Pickup</legend>
          <label>
            Address
            <input value={pickupAddress} onChange={(e) => setPickupAddress(e.target.value)} required />
          </label>
          <div className="coordinate-row">
            <label>
              Latitude
              <input
                type="number"
                step="any"
                value={pickupLat}
                onChange={(e) => setPickupLat(e.target.value)}
                required
              />
            </label>
            <label>
              Longitude
              <input
                type="number"
                step="any"
                value={pickupLng}
                onChange={(e) => setPickupLng(e.target.value)}
                required
              />
            </label>
          </div>
        </fieldset>

        <fieldset>
          <legend>Destination</legend>
          <label>
            Address
            <input value={destinationAddress} onChange={(e) => setDestinationAddress(e.target.value)} required />
          </label>
          <div className="coordinate-row">
            <label>
              Latitude
              <input
                type="number"
                step="any"
                value={destinationLat}
                onChange={(e) => setDestinationLat(e.target.value)}
                required
              />
            </label>
            <label>
              Longitude
              <input
                type="number"
                step="any"
                value={destinationLng}
                onChange={(e) => setDestinationLng(e.target.value)}
                required
              />
            </label>
          </div>
        </fieldset>

        <label>
          Departure
          <input
            type="datetime-local"
            value={departureTime}
            onChange={(e) => setDepartureTime(e.target.value)}
            required
          />
        </label>
        <label>
          Flexible by (minutes)
          <input
            type="number"
            min={0}
            max={180}
            value={timeFlexibility}
            onChange={(e) => setTimeFlexibility(Number(e.target.value))}
          />
        </label>
        <label>
          Passengers
          <input
            type="number"
            min={1}
            max={6}
            value={passengerCount}
            onChange={(e) => setPassengerCount(Number(e.target.value))}
          />
        </label>

        {error && <p className="form-error">{error}</p>}
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Posting…" : "Find Matches"}
        </button>
      </form>
    </section>
  );
}
