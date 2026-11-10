---
name: vn-law-check
description: Rà soát/audit một website hoặc mobile app theo pháp luật Việt Nam về bảo vệ dữ liệu cá nhân, thương mại điện tử, an ninh mạng, bảo vệ người tiêu dùng, quảng cáo trực tuyến, giao dịch điện tử và minh bạch AI. Dùng khi người dùng yêu cầu audit/kiểm tra/rà soát pháp lý website theo luật VN, hỏi về tuân thủ NĐ 356/2025, Luật Bảo vệ dữ liệu cá nhân, Luật Thương mại điện tử 2025, hoặc cần checklist compliance cho site Việt Nam. Also use for English requests: Vietnam legal compliance audit, Vietnamese privacy law (PDPL), Decree 356/2025, Vietnam e-commerce law, Vietnam cybersecurity law, website or mobile app compliance check for Vietnamese users.
---

# VN Web Compliance Audit

Rà soát (audit) một website theo quy định pháp luật Việt Nam hiện hành liên quan đến: bảo vệ dữ liệu cá nhân, thương mại điện tử, an ninh mạng/lưu trữ dữ liệu, bảo vệ người tiêu dùng, quảng cáo trực tuyến, giao dịch điện tử, và minh bạch AI (nếu áp dụng).

## Nguyên tắc bắt buộc

1. **Không khẳng định dứt khoát** "website này vi phạm/không vi phạm pháp luật". Đây là công cụ hỗ trợ rà soát ban đầu, không phải tư vấn pháp lý chính thức.
2. **Luôn trích dẫn số hiệu văn bản pháp luật cụ thể** (số văn bản, ngày ban hành/hiệu lực, điều khoản nếu biết) cho mỗi mục kiểm tra. Không bịa số hiệu. Nếu không chắc, nói rõ "cần tra cứu lại".
3. Luật Việt Nam về dữ liệu cá nhân, TMĐT, an ninh mạng đang trong giai đoạn chuyển tiếp mạnh (nhiều luật mới 2025 có hiệu lực trong 2026, một số nghị định xử phạt chưa ban hành hoặc chưa xác minh được). Mục nào checklist ghi "CHƯA XÁC MINH" thì chỉ dẫn tên văn bản, không tự điền số điều hay mức phạt. Luôn khuyến nghị người dùng xác minh lại văn bản còn hiệu lực tại thuvienphapluat.vn hoặc vbpl.vn.
4. Mỗi phát hiện phân loại mức độ: 🔴 Cần xử lý ngay / 🟡 Nên cải thiện / 🟢 Đạt yêu cầu / ⚪ Không áp dụng.
5. Luôn khuyến nghị tham vấn luật sư cho quyết định cuối cùng, đặc biệt với mục 🔴.
6. Tự xác định loại hình website bằng cách quét code/nội dung thực tế (xem `references/00-triage.md`). Không đoán bừa, nhưng cũng không hỏi người dùng nếu quét được. Chỉ hỏi lại khi quét xong vẫn không xác định được.

## Quy trình

1. **Luôn bắt đầu bằng `references/00-triage.md`**: phân loại mức độ phức tạp (tĩnh/thu thập nhẹ/bán hàng/nền tảng quy mô) trước khi mở checklist nào. Chạy `bash scripts/scan.sh <thư-mục-code>`, hoặc `bash scripts/scan.sh <URL>` nếu chỉ có địa chỉ website, để quét tự động, rồi xem lại bằng chứng script in ra. Site tĩnh không form, không script theo dõi, không bán hàng thì KHÔNG audit đủ bộ checklist.
2. Theo bảng phân loại ở bước 1, chỉ mở checklist thực sự áp dụng tại `references/`: 01-personal-data-protection, 02-ecommerce, 03-cybersecurity, 04-consumer-protection, 05-advertising, 06-electronic-transactions, 07-ai-transparency (luôn thêm nếu có chatbot/nội dung AI), 08-penalties-reference, 09-mobile-app (luôn thêm nếu là mobile app).
3. Đọc code/nội dung website thực tế (footer, trang chính sách, cookie banner, form thu thập dữ liệu) để xác định trạng thái. Chưa kiểm tra thì không suy đoán.
4. Xuất báo cáo theo mẫu `examples/sample-audit-report.md`. Với site mức 0-1, dùng bản rút gọn, không liệt kê các checklist không áp dụng thành bảng dài.
5. Luôn đóng báo cáo bằng phần "Giới hạn & Khuyến nghị" (xem `DISCLAIMER.md`).

Nguồn pháp luật đầy đủ: `sources/legal-references.md`.
