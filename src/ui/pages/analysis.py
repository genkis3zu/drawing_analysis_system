# src/ui/pages/analysis.py

[Previous content omitted for brevity]

                # 処理完了
                st.session_state.processing_status = '完了'
                NotificationManager.show_success("解析が完了しました")
                
                # 結果タブに切り替え
                st.session_state.active_tab = "📊 解析結果"
                st.rerun()
                
            finally:
                # 一時ファイルの削除
                try:
                    Path(temp_path).unlink()
                except:
                    pass
                
    except Exception as e:
        st.session_state.processing_status = 'エラー'
        NotificationManager.show_error(f"解析エラー: {e}")
