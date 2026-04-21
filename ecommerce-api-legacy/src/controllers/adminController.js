const reportModel = require('../models/reportModel');

async function getFinancialReport() {
  const rows = await reportModel.fetchFinancialRows();
  const reportByCourse = new Map();

  rows.forEach((row) => {
    if (!reportByCourse.has(row.course_id)) {
      reportByCourse.set(row.course_id, {
        course: row.course_title,
        revenue: 0,
        students: [],
      });
    }

    const currentCourse = reportByCourse.get(row.course_id);

    if (row.user_name) {
      currentCourse.students.push({
        student: row.user_name,
        paid: row.payment_amount || 0,
      });
    }

    if (row.payment_status === 'PAID') {
      currentCourse.revenue += row.payment_amount || 0;
    }
  });

  return Array.from(reportByCourse.values());
}

module.exports = { getFinancialReport };
