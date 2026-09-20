import { createSignal, onMount } from 'solid-js'
import { For, Show } from 'solid-js'
import { api, getUser } from '../api/client'
import type { Shed, ShiftHandover } from '../types'

const empty = { name: '', location: '', notes: '' }
const emptyHandover = { shedId: '', phrase: '', handedBy: '', takenBy: '' }

export default function Sheds() {
  const currentUser = getUser()
  const isAdmin = currentUser?.role === 'admin'

  const [rows, setRows] = createSignal<Shed[]>([])
  const [handovers, setHandovers] = createSignal<ShiftHandover[]>([])
  const [form, setForm] = createSignal({ ...empty })
  const [handoverForm, setHandoverForm] = createSignal({
    ...emptyHandover,
    handedBy: currentUser?.username ?? '',
  })
  const [error, setError] = createSignal('')

  async function load() {
    const [shedList, openList] = await Promise.all([
      api<Shed[]>('/api/sheds'),
      api<ShiftHandover[]>('/api/shift-handovers?open=1'),
    ])
    setRows(shedList)
    setHandovers(openList)
  }

  onMount(() => {
    load().catch((e) => setError(e.message))
  })

  function openHandoversFor(shedId: number) {
    return handovers().filter((h) => h.shedId === shedId)
  }

  async function onSubmit(e: Event) {
    e.preventDefault()
    setError('')
    try {
      await api('/api/sheds', {
        method: 'POST',
        body: JSON.stringify(form()),
      })
      setForm({ ...empty })
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败')
    }
  }

  async function onOpenHandover(e: Event) {
    e.preventDefault()
    setError('')
    try {
      await api('/api/shift-handovers', {
        method: 'POST',
        body: JSON.stringify({
          shedId: Number(handoverForm().shedId),
          phrase: handoverForm().phrase,
          handedBy: handoverForm().handedBy,
          takenBy: handoverForm().takenBy,
        }),
      })
      setHandoverForm({ ...emptyHandover, handedBy: currentUser?.username ?? '' })
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : '开交接失败')
    }
  }

  async function closeHandover(id: number) {
    if (!confirm('确认关闭该交接班口令？')) return
    setError('')
    try {
      await api(`/api/shift-handovers/${id}/close`, { method: 'POST' })
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : '关闭失败')
    }
  }

  async function remove(id: number) {
    if (!confirm('确认删除该菇房？')) return
    try {
      await api(`/api/sheds/${id}`, { method: 'DELETE' })
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败')
    }
  }

  return (
    <div>
      <header class="page-header">
        <h1>菇房</h1>
        <p class="muted">登记场区位置与备注</p>
      </header>
      {error() && <div class="error">{error()}</div>}

      <form class="panel form-grid" onSubmit={onSubmit}>
        <label>
          名称
          <input
            value={form().name}
            onInput={(e) => setForm({ ...form(), name: e.currentTarget.value })}
            required
          />
        </label>
        <label>
          位置
          <input
            value={form().location}
            onInput={(e) => setForm({ ...form(), location: e.currentTarget.value })}
            required
          />
        </label>
        <label class="span-2">
          备注
          <input
            value={form().notes ?? ''}
            onInput={(e) => setForm({ ...form(), notes: e.currentTarget.value })}
          />
        </label>
        <button type="submit" class="btn primary">
          新增菇房
        </button>
      </form>

      <form class="panel form-grid" onSubmit={onOpenHandover}>
        <label>
          菇房
          <select
            value={handoverForm().shedId}
            onChange={(e) => setHandoverForm({ ...handoverForm(), shedId: e.currentTarget.value })}
            required
          >
            <option value="">选择菇房</option>
            <For each={rows()}>
              {(s) => <option value={String(s.id)}>{s.name}</option>}
            </For>
          </select>
        </label>
        <label>
          交接口令
          <input
            value={handoverForm().phrase}
            onInput={(e) => setHandoverForm({ ...handoverForm(), phrase: e.currentTarget.value })}
            placeholder="去空白后 4–12 字"
            required
          />
        </label>
        <label>
          交班人
          <input
            value={handoverForm().handedBy}
            onInput={(e) => setHandoverForm({ ...handoverForm(), handedBy: e.currentTarget.value })}
            placeholder="登录名"
            required
          />
        </label>
        <label>
          接班人
          <input
            value={handoverForm().takenBy}
            onInput={(e) => setHandoverForm({ ...handoverForm(), takenBy: e.currentTarget.value })}
            placeholder="登录名，须与交班人不同"
            required
          />
        </label>
        <button type="submit" class="btn primary">
          开交接班
        </button>
        <p class="muted span-2">按东八区自然日归日，同棚同日仅一张；口令未关闭前，该棚出菇室不可置为 fruiting。</p>
      </form>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>名称</th>
              <th>位置</th>
              <th>备注</th>
              <th>交接班口令</th>
              <th />
            </tr>
          </thead>
          <tbody>
            <For each={rows()}>
              {(r) => (
                <tr>
                  <td>{r.id}</td>
                  <td>{r.name}</td>
                  <td>{r.location}</td>
                  <td>{r.notes || '—'}</td>
                  <td>
                    <Show
                      when={openHandoversFor(r.id).length > 0}
                      fallback={<span class="muted">—</span>}
                    >
                      <For each={openHandoversFor(r.id)}>
                        {(h) => (
                          <div class="handover-chip">
                            <span class="badge handover">{h.phrase}</span>
                            <span class="muted">
                              {h.workDate} · {h.handedBy} → {h.takenBy}
                            </span>
                            <Show when={isAdmin}>
                              <button
                                type="button"
                                class="btn ghost"
                                onClick={() => closeHandover(h.id)}
                              >
                                关闭
                              </button>
                            </Show>
                          </div>
                        )}
                      </For>
                    </Show>
                  </td>
                  <td>
                    <button type="button" class="btn ghost" onClick={() => remove(r.id)}>
                      删除
                    </button>
                  </td>
                </tr>
              )}
            </For>
          </tbody>
        </table>
      </div>
    </div>
  )
}
