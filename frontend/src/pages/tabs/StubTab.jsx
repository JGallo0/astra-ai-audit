export default function StubTab({ icon, title, desc }) {
  return (
    <div className="card">
      <div className="empty-state">
        <div className="empty-state-icon">{icon}</div>
        <div className="empty-state-title">{title}</div>
        <div className="empty-state-sub">{desc}</div>
        <div className="badge badge-amber" style={{ marginTop: 8 }}>Em desenvolvimento</div>
      </div>
    </div>
  )
}
