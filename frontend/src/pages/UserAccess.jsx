export default function UserAccess() {
  const users = [
    { email: 'admin@astrasolar.com.br', role: 'admin',    limit_chat: 9999, limit_audit: 9999 },
    { email: 'ia.carbon@astrasolar.com.br', role: 'internal', limit_chat: 500, limit_audit: 50 },
  ]

  const ROLE_CLS = { admin: 'badge-red', internal: 'badge-blue', pilot_client: 'badge-amber' }

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Acesso de Usuários</div>
        <div className="page-subtitle">Gestão de papéis e limites de uso</div>
      </div>

      <div className="card">
        <div className="flex items-center justify-between" style={{ marginBottom: 16 }}>
          <div className="card-title" style={{ marginBottom: 0 }}>Usuários autorizados</div>
          <button className="btn btn-outline btn-sm">+ Convidar usuário</button>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>E-mail</th>
                <th>Papel</th>
                <th>Limite Chat/mês</th>
                <th>Limite Auditoria/mês</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.email}>
                  <td style={{ fontWeight: 600 }}>{u.email}</td>
                  <td><span className={`badge ${ROLE_CLS[u.role] || 'badge-gray'}`}>{u.role}</span></td>
                  <td>{u.limit_chat === 9999 ? '∞' : u.limit_chat}</td>
                  <td>{u.limit_audit === 9999 ? '∞' : u.limit_audit}</td>
                  <td>
                    <button className="btn btn-sm btn-ghost">Editar</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="alert alert-info" style={{ marginTop: 16 }}>
          Integração com Google OAuth via Supabase Auth. Acesso concedido por whitelist de e-mails.
        </div>
      </div>

      <div className="card">
        <div className="card-title">Papéis e permissões</div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Papel</th>
                <th>Chat</th>
                <th>Auditoria</th>
                <th>Admin</th>
              </tr>
            </thead>
            <tbody>
              {[
                { role: 'admin',        chat: '∞',   audit: '∞',   admin: '✅' },
                { role: 'internal',     chat: '500', audit: '50',  admin: '❌' },
                { role: 'pilot_client', chat: '50',  audit: '5',   admin: '❌' },
              ].map(r => (
                <tr key={r.role}>
                  <td><span className={`badge ${ROLE_CLS[r.role] || 'badge-gray'}`}>{r.role}</span></td>
                  <td>{r.chat}</td>
                  <td>{r.audit}</td>
                  <td>{r.admin}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
