import { useState } from "react";
import Layout from "../components/Layout.jsx";
import StationsScreen from "../components/screens/Stations.jsx";
import StationModal from "../components/Modals/StationModal.jsx";
import "./Pages.css";

export default function Stations() {
  const [modalMode, setModalMode] = useState(null); // 'add' | 'edit'
  const [editStation, setEditStation] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const openModal = (type, data = null) => {
    if (type === "addStation") {
      setModalMode("add");
      setEditStation(null);
    } else if (type === "editStation") {
      setModalMode("edit");
      setEditStation(data);
    }
  };

  const handleSaved = () => {
    setModalMode(null);
    setRefreshKey((k) => k + 1);
  };

  return (
    <Layout>
      <StationsScreen openModal={openModal} refreshKey={refreshKey} />
      <StationModal
        isOpen={!!modalMode}
        onClose={() => setModalMode(null)}
        mode={modalMode || "add"}
        station={editStation}
        onSaved={handleSaved}
      />
    </Layout>
  );
}
