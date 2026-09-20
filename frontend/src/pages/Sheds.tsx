import { createSignal, onMount } from 'solid-js'
import { For, Show } from 'solid-js'
import { api } from '../api/client'
import type { CurrentUser, Shed } from '../types'

const empty = { name: '', location: '', notes: '' }
const emptyHandover = { shedId: '', phrase: '', handedBy: '', takenBy: '' }

export default function Sheds() {
  const [rows, setRows] = createSignal<Shed[]>([])
  const [me, setMe] = createSignal<CurrentUser | null>(null)
  const [openTotal, setOpenTotal] = createSignal(0)
  const [form, setForm] = createSignal({ ...empty })
  const [hoForm, setHoForm] = createSignal({ ...emptyHandover })
  const [error, setError] = createSignal('')

  async function load() {
    const [shedData, meData, openCheck] = await Promise.all([
      api<Shed[]>('/api/sheds'),
      api<CurrentUser>('/api/auth/me'),
      api<{ total: number }>('/api/shift-handovers/open-check'),
    ])
    setRows(shedData)
    setMe(meData)
    setOpenTotal(openCheck.total)
    if (!hoForm().handedBy) {
      setHoForm({ ...hoForm(), handedBy: meData.username })
    }
  }

  onMount(() => {
    load().catch((e) => setError(e.message))
  })

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
          shedId: Number(hoForm().shedId),
          phrase: hoForm().phrase,
          handedBy: hoForm().handedBy,
          takenBy: hoForm().takenBy,
        }),
      })
      setHoForm({ ...emptyHandover, handedBy: me()?.username ?? '' })
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : '开交接失败')
    }
  }

  async function closeHandover(id: number) {
    if (!confirm('确认关闭该交接班口令？关闭后该菇房出菇室才放行 fruiting。')) return
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
        <p class="muted">登记场区位置与备注 · 未关闭交接班 {openTotal()} 张</p>
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
          交接菇房
          <select
            value={hoForm().shedId}
            onChange={(e) => setHoForm({ ...hoForm(), shedId: e.currentTarget.value })}
            required
          >
            <option value="">选择菇房</option>
            <For each={rows().filter((s) => !s.openHandover)}>
              {(s) => <option value={String(s.id)}>{s.name}</option>}
            </For>
          </select>
        </label>
        <label>
          交接班口令（去空白后 4–12 字）
          <input
            value={hoForm().phrase}
            onInput={(e) => setHoForm({ ...hoForm(), phrase: e.currentTarget.value })}
            required
          />
        </label>
        <label>
          交班人（登录名）
          <input
            value={hoForm().handedBy}
            onInput={(e) => setHoForm({ ...hoForm(), handedBy: e.currentTarget.value })}
            placeholder={me()?.username ?? ''}
          />
        </label>
        <label>
          接班人（登录名）
          <input
            value={hoForm().takenBy}
            onInput={(e) => setHoForm({ ...hoForm(), takenBy: e.currentTarget.value })}
            required
          />
        </label>
        <button type="submit" class="btn primary">
          开交接班
        </button>
        <p class="hint span-2">
          同棚同日仅一张；未关闭时该菇房出菇室不可写入 fruiting，关闭仅场长可操作。
        </p>
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
                    <Show when={r.openHandover} fallback="—">
                      {(ho) => (
                        <span class="handover-cell">
                          <span class="badge fruiting">{ho().phrase}</span>{' '}
                          <small class="muted">
                            {ho().workDate} · {ho().handedBy} → {ho().takenBy}
                          </small>{' '}
                          <Show when={me()?.role === 'admin'}>
                            <button
                              type="button"
                              class="btn ghost"
                              onClick={() => closeHandover(ho().id)}
                            >
                              关闭交接
                            </button>
                          </Show>
                        </span>
                      )}
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
