import { useState } from "react";
import Layout from "../components/Layout.jsx";
import CaseManagementScreen from "../components/screens/CaseManagement.jsx";
import NewCaseModal from "../components/Modals/NewCaseModal.jsx";
import "./Pages.css";

export default function CaseManagement() {
  const [newCaseOpen, setNewCaseOpen] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const openModal = (type) => {
    if (type === "newCase") setNewCaseOpen(true);
  };

  const handleCreated = () => {
    setNewCaseOpen(false);
    setRefreshKey((k) => k + 1);
  };

  return (
    <Layout>
      <CaseManagementScreen openModal={openModal} refreshKey={refreshKey} />
      <NewCaseModal
        isOpen={newCaseOpen}
        onClose={() => setNewCaseOpen(false)}
        onCreated={handleCreated}
      />
    </Layout>
  );
}
