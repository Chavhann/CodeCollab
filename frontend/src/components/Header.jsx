function Header({ user, onLogout }) {
  return (
    <header className="app-header">
      <div className="brand">
        <span className="brand-mark">{`{ }`}</span>
        <span className="brand-name">CodeCollab</span>
      </div>

      <div className="header-right">
        <span className="connection-status">
          <span className="status-dot"></span>
          Connected
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
