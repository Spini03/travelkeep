import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Parsea una fecha en formato ISO (YYYY-MM-DD) como fecha local,
 * evitando problemas de zona horaria que pueden causar que la fecha
 * se muestre incorrectamente (un día antes o después).
 * 
 * @param dateString - Fecha en formato ISO (YYYY-MM-DD)
 * @returns Objeto Date parseado como fecha local
 */
export function parseLocalDate(dateString: string): Date {
  const [year, month, day] = dateString.split('-').map(Number);
  return new Date(year, month - 1, day);
}

/**
 * Formatea una fecha local como ISO (YYYY-MM-DD) sin pasar por UTC —
 * inverso de parseLocalDate. date.toISOString() convierte a UTC primero,
 * lo que corre la fecha un día para atrás en husos horarios adelantados a UTC.
 */
export function toLocalDateString(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}
