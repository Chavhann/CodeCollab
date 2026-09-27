function Header({ user, onLogout, connectionStatus = "disconnected", presence = [] }) {
  return (
    <header className="app-header">
      <div className="brand">
        <span className="brand-mark">{`{ }`}</span>
        <span className="brand-name">CodeCollab</span>
      </div>

      <div className="header-right">
        <div className="collaborators">
          <span className="collaborators-label">
            Collaborators {presence.length > 0 ? `(${presence.length})` : ""}
          </span>
          {presence.length > 0 && (
            <div className="collaborator-list">
              {presence.map((collaborator) => (
                <span className="collaborator" key={collaborator.user_id}>
                  <span className="collaborator-dot"></span>
                  {collaborator.username}
                </span>
              ))}
            </div>
          )}
        </div>

        <span className={`connection-status connection-${connectionStatus}`}>
          <span className="status-dot"></span>
          {connectionStatus === "connected"
            ? "Connected"
            : connectionStatus === "connecting"
              ? "Connecting..."
              : "Disconnected"}
        </span>

        <span className="user-name">
          {user?.username || user?.email || "Developer"}
        </span>

        <button
          className="logout-button"
          type="button"
          onClick={onLogout}
        >
          Logout
        </button>
      </div>
    </header>
  );
}

export default Header;




