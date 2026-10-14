// The admin section is Uzbek-only for now, whatever language the admin chose
// for the shop. These helpers pin shared texts and prices to Uzbek.
import i18n from '../../i18n'
import { dateTime as formatDateTime, money as formatMoney } from '../../lib/format'

export const t = i18n.getFixedT('uz')
export const money = (amount) => formatMoney(amount, 'uz')
export const dateTime = (iso) => formatDateTime(iso, 'uz')
